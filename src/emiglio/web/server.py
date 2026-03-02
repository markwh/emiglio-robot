"""FastAPI web server with WebSocket for real-time robot control."""

import asyncio
import io
import json
import logging
import math
import struct
import wave
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from typing import Optional

from emiglio.event_bus import EventBus
from emiglio.models import Events, MotorCommand, JoystickInput
from emiglio.locomotion.controller import LocomotionController
from emiglio.vision.camera import Camera
from emiglio.vision.stream import stream_response
from emiglio.conversation import ConversationManager
from emiglio.rl.training import TrainingManager, TrainingStats, TrainingEpisode

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


def create_app(
    bus: EventBus,
    locomotion: LocomotionController,
    camera: Camera | None = None,
    conversation: ConversationManager | None = None,
) -> FastAPI:
    app = FastAPI(title="Emiglio Robot")
    connected_clients: set[WebSocket] = set()
    training_mgr = TrainingManager()
    _training_broadcast_task: asyncio.Task | None = None

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # -- Broadcast helpers --
    async def _broadcast(msg: dict) -> None:
        """Send a JSON message to all connected WebSocket clients."""
        for client in list(connected_clients):
            try:
                await client.send_json(msg)
            except Exception:
                connected_clients.discard(client)

    async def _broadcast_motor_state(command: MotorCommand) -> None:
        await _broadcast({
            "type": "motor_state",
            "left": command.left,
            "right": command.right,
        })

    async def _broadcast_event(event: str, detail: str = "") -> None:
        await _broadcast({"type": "event", "event": event, "detail": detail})

    bus.subscribe(Events.MOTOR_COMMAND, _broadcast_motor_state)

    # -- Routes --
    @app.get("/")
    async def index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "subsystems": {
                "camera": camera is not None and camera.get_jpeg() is not None,
                "audio": conversation is not None and conversation._capture is not None,
                "brain": conversation is not None,
            },
        }

    @app.get("/stream")
    async def camera_stream():
        if camera is None:
            return {"error": "No camera available"}
        return stream_response(camera)

    @app.get("/camera/devices")
    async def camera_devices():
        devices = Camera.list_devices()
        active = camera.active_index if camera is not None else None
        return {"devices": devices, "active_index": active}

    class CameraSwitchRequest(BaseModel):
        index: int

    @app.post("/camera/switch")
    async def camera_switch(req: CameraSwitchRequest):
        if camera is None:
            return {"error": "No camera available"}
        try:
            await asyncio.to_thread(camera.switch, req.index)
            return {"ok": True, "active_index": camera.active_index}
        except Exception as e:
            logger.error("Camera switch failed: %s", e)
            return {"error": str(e)}

    @app.post("/audio/test")
    async def audio_test():
        """Play a short test tone to verify audio output works."""
        if conversation is None or conversation._playback is None:
            return {"ok": False, "error": "Audio playback not available"}
        try:
            wav_bytes = _generate_test_tone()
            await conversation._playback.play_wav(wav_bytes)
            return {"ok": True, "message": "Test tone played (440Hz, 0.5s)"}
        except Exception as e:
            logger.error("Audio test failed: %s", e)
            return {"ok": False, "error": str(e)}

    @app.post("/tts/test")
    async def tts_test():
        """Synthesize and play a short phrase to test the full TTS pipeline."""
        if conversation is None:
            return {"ok": False, "error": "Conversation manager not available"}
        if conversation._tts is None or not conversation._tts.available:
            return {"ok": False, "error": "TTS not available"}
        if conversation._playback is None:
            return {"ok": False, "error": "Audio playback not available"}
        try:
            from emiglio.config import settings
            audio = await conversation._tts.synthesize(
                "Hello, I am Emiglio.", server_url=settings.server_tts_url
            )
            if audio is None:
                return {"ok": False, "error": "TTS returned no audio"}
            await conversation._playback.play_wav(audio)
            return {"ok": True, "message": "TTS test played successfully"}
        except Exception as e:
            logger.error("TTS test failed: %s", e)
            return {"ok": False, "error": str(e)}

    # -- Voice Lab endpoints --

    class VoicePreviewRequest(BaseModel):
        text: str
        voice_id: str
        model_id: Optional[str] = None

    class VoiceActivateRequest(BaseModel):
        voice_id: str

    @app.get("/voicelab/voices")
    async def voicelab_voices():
        if conversation is None or conversation._tts is None:
            return {"ok": False, "error": "TTS not available"}
        voices = await conversation._tts.list_voices()
        return {
            "ok": True,
            "voices": voices,
            "active_voice_id": conversation._tts.voice_id,
        }

    @app.post("/voicelab/preview")
    async def voicelab_preview(req: VoicePreviewRequest):
        if conversation is None or conversation._tts is None or not conversation._tts.available:
            return {"ok": False, "error": "TTS not available"}
        try:
            audio = await conversation._tts.synthesize(
                text=req.text,
                voice_id=req.voice_id,
                model_id=req.model_id,
            )
            if audio is None:
                return {"ok": False, "error": "Synthesis returned no audio"}
            return Response(content=audio, media_type="audio/wav")
        except Exception as e:
            logger.error("Voice preview failed: %s", e)
            return {"ok": False, "error": str(e)}

    @app.post("/voicelab/activate")
    async def voicelab_activate(req: VoiceActivateRequest):
        if conversation is None or conversation._tts is None:
            return {"ok": False, "error": "TTS not available"}
        conversation._tts.set_voice(req.voice_id)
        return {"ok": True, "active_voice_id": conversation._tts.voice_id}

    async def _broadcast_training() -> None:
        """Drain the training queue and send updates to all WS clients."""
        nonlocal _training_broadcast_task
        mgr = training_mgr
        try:
            while mgr.running or not mgr.queue.empty():
                try:
                    item = await asyncio.wait_for(mgr.queue.get(), timeout=0.2)
                except asyncio.TimeoutError:
                    continue

                if item is None:  # sentinel — training thread finished
                    break

                if isinstance(item, TrainingEpisode):
                    # Downsample trajectory to max 200 points
                    traj = item.trajectory
                    if len(traj) > 200:
                        step = len(traj) / 200
                        traj = [traj[int(i * step)] for i in range(200)]
                    await _broadcast({
                        "type": "training_episode",
                        "episode": item.stats.episode,
                        "reward": round(item.stats.reward, 3),
                        "length": item.stats.length,
                        "goal_reached": item.stats.goal_reached,
                        "dist_to_goal": round(item.stats.dist_to_goal, 1),
                        "trajectory": [[round(x, 1), round(y, 1)] for x, y, _ in traj],
                        "goal": [round(item.goal[0], 1), round(item.goal[1], 1)],
                    })
                elif isinstance(item, TrainingStats):
                    await _broadcast({
                        "type": "training_stats",
                        "episode": item.episode,
                        "reward": round(item.reward, 3),
                        "length": item.length,
                        "goal_reached": item.goal_reached,
                        "dist_to_goal": round(item.dist_to_goal, 1),
                    })
        except Exception:
            logger.exception("Training broadcast error")
        finally:
            await _broadcast({"type": "training_status", "running": False})
            _training_broadcast_task = None

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await ws.accept()
        connected_clients.add(ws)
        logger.info("WebSocket client connected")
        try:
            # Send initial subsystem status
            await ws.send_json({
                "type": "subsystem_status",
                "motors": True,
                "camera": camera is not None and camera.get_jpeg() is not None,
                "audio": conversation is not None and conversation._capture is not None,
                "brain": conversation is not None,
            })

            while True:
                raw = await ws.receive_text()
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON from WebSocket: %s", raw)
                    continue

                msg_type = data.get("type")
                if msg_type == "joystick":
                    joy = JoystickInput(
                        x=float(data.get("x", 0)),
                        y=float(data.get("y", 0)),
                    )
                    command = LocomotionController.joystick_to_motor(joy)
                    await bus.publish(Events.MOTOR_COMMAND, command)

                elif msg_type == "stop":
                    await bus.publish(Events.MOTOR_COMMAND, MotorCommand(0, 0))
                    await _broadcast_event("stop", "Emergency stop")

                elif msg_type == "talk":
                    # Push-to-talk: trigger voice interaction
                    if conversation is None:
                        await ws.send_json({"type": "status", "message": "Voice not available"})
                        continue
                    if conversation.busy:
                        await ws.send_json({"type": "status", "message": "Already listening..."})
                        continue

                    await _broadcast_event("voice", "Push-to-talk activated")

                    async def send_status(msg: str):
                        await ws.send_json({"type": "status", "message": msg})
                        await _broadcast_event("conversation", msg)

                    asyncio.create_task(
                        _run_conversation(conversation, ws, send_status, voice=True)
                    )

                elif msg_type == "skill":
                    # Expressive skill: spin, wiggle, dance
                    skill_name = data.get("name", "")
                    speed = float(data.get("speed", 1.0))
                    duration = float(data.get("duration", 1.0))
                    valid_skills = {"spin", "wiggle", "dance"}
                    if skill_name not in valid_skills:
                        await ws.send_json({"type": "status", "message": f"Unknown skill: {skill_name}"})
                        continue
                    if conversation is None:
                        await ws.send_json({"type": "status", "message": "Movement not available"})
                        continue
                    await _broadcast_event("skill", f"{skill_name} speed={speed:.1f} duration={duration:.1f}s")
                    cmd = {"action": "move", "params": skill_name, "speed": speed, "duration": duration}
                    asyncio.create_task(conversation._execute_command(cmd))

                elif msg_type == "text":
                    # Text input from chat box
                    text = data.get("text", "").strip()
                    if not text:
                        continue
                    if conversation is None:
                        await ws.send_json({"type": "status", "message": "Brain not available"})
                        continue
                    if conversation.busy:
                        await ws.send_json({"type": "status", "message": "Still thinking..."})
                        continue

                    await _broadcast_event("text", text)

                    async def send_status_text(msg: str):
                        await ws.send_json({"type": "status", "message": msg})
                        await _broadcast_event("conversation", msg)

                    asyncio.create_task(
                        _run_conversation(
                            conversation, ws, send_status_text, voice=False, text=text
                        )
                    )

                elif msg_type == "training_start":
                    nonlocal _training_broadcast_task
                    if training_mgr.running:
                        await ws.send_json({"type": "status", "message": "Training already running"})
                        continue
                    total = int(data.get("total_timesteps", 100_000))
                    interval = int(data.get("demo_interval", 1))
                    lr = float(data.get("learning_rate", 3e-4))
                    await training_mgr.start_training(total, interval, lr)
                    await _broadcast({"type": "training_status", "running": True})
                    await _broadcast_event("training", f"Started (timesteps={total}, interval={interval})")
                    _training_broadcast_task = asyncio.create_task(_broadcast_training())

                elif msg_type == "training_stop":
                    training_mgr.stop_training()
                    await _broadcast_event("training", "Stop requested")

                elif msg_type == "training_config":
                    interval = int(data.get("demo_interval", 1))
                    training_mgr.set_demo_interval(interval)
                    await _broadcast_event("training", f"Demo interval → {interval}")

                else:
                    logger.warning("Unknown WebSocket message type: %s", msg_type)
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
            await bus.publish(Events.MOTOR_COMMAND, MotorCommand(0, 0))
        finally:
            connected_clients.discard(ws)

    return app


async def _run_conversation(
    conversation: ConversationManager,
    ws: WebSocket,
    status_callback,
    voice: bool = True,
    text: str = "",
) -> None:
    """Run a conversation interaction and send results to the WebSocket."""
    try:
        if voice:
            result = await conversation.handle_voice_interaction(status_callback)
        else:
            result = await conversation.handle_text_interaction(text, status_callback)

        await ws.send_json({"type": "conversation_result", **result})
    except Exception as e:
        logger.error("Conversation task error: %s", e)
        try:
            await ws.send_json({"type": "status", "message": "Error occurred"})
        except Exception:
            pass


def _generate_test_tone(
    freq: float = 440.0, duration: float = 0.5, sample_rate: int = 22050, volume: float = 0.5
) -> bytes:
    """Generate a WAV sine wave tone for audio testing."""
    n_samples = int(sample_rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        for i in range(n_samples):
            sample = int(volume * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
            wf.writeframes(struct.pack("<h", sample))
    return buf.getvalue()
