"""FastAPI web server with WebSocket for real-time robot control."""

import asyncio
import json
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from emiglio.event_bus import EventBus
from emiglio.models import Events, MotorCommand, JoystickInput
from emiglio.locomotion.controller import LocomotionController
from emiglio.vision.camera import Camera
from emiglio.vision.stream import stream_response
from emiglio.conversation import ConversationManager

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


def create_app(
    bus: EventBus,
    locomotion: LocomotionController,
    camera: Camera | None = None,
    conversation: ConversationManager | None = None,
) -> FastAPI:
    app = FastAPI(title="Emiglio Robot")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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

    @app.websocket("/ws")
    async def websocket_endpoint(ws: WebSocket):
        await ws.accept()
        logger.info("WebSocket client connected")
        try:
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

                elif msg_type == "talk":
                    # Push-to-talk: trigger voice interaction
                    if conversation is None:
                        await ws.send_json({"type": "status", "message": "Voice not available"})
                        continue
                    if conversation.busy:
                        await ws.send_json({"type": "status", "message": "Already listening..."})
                        continue

                    async def send_status(msg: str):
                        await ws.send_json({"type": "status", "message": msg})

                    # Run conversation in background so WebSocket stays responsive
                    asyncio.create_task(
                        _run_conversation(conversation, ws, send_status, voice=True)
                    )

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

                    async def send_status_text(msg: str):
                        await ws.send_json({"type": "status", "message": msg})

                    asyncio.create_task(
                        _run_conversation(
                            conversation, ws, send_status_text, voice=False, text=text
                        )
                    )

                else:
                    logger.warning("Unknown WebSocket message type: %s", msg_type)
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
            await bus.publish(Events.MOTOR_COMMAND, MotorCommand(0, 0))

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
