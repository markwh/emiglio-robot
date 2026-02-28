"""Conversation manager — orchestrates the full voice interaction loop.

Flow: mic capture → STT (server) → brain (server) → TTS (server) → speaker + motor commands.
"""

import asyncio
import base64
import logging

import httpx

from emiglio.config import settings
from emiglio.event_bus import EventBus
from emiglio.models import Events, MotorCommand
from emiglio.vision.camera import Camera

logger = logging.getLogger(__name__)

# Movement presets: direction → (left, right) motor speeds
MOVE_PRESETS = {
    "forward": (0.6, 0.6),
    "backward": (-0.6, -0.6),
    "left": (-0.5, 0.5),
    "right": (0.5, -0.5),
    "stop": (0.0, 0.0),
}

MOVE_DURATION = 1.0  # seconds to hold a movement command


class ConversationManager:
    """Ties together audio, STT, brain, TTS, and locomotion."""

    def __init__(
        self,
        bus: EventBus,
        camera: Camera | None = None,
        audio_capture=None,
        audio_playback=None,
    ) -> None:
        self._bus = bus
        self._camera = camera
        self._capture = audio_capture
        self._playback = audio_playback
        self._client = httpx.AsyncClient(timeout=30.0)
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    async def handle_voice_interaction(self, status_callback=None) -> dict:
        """Run one full voice interaction cycle.

        Returns dict with keys: transcript, reply, commands, error.
        status_callback is an optional async callable(str) for progress updates.
        """
        if self._busy:
            return {"error": "Already processing"}
        self._busy = True

        async def status(msg: str):
            logger.info("Conversation: %s", msg)
            if status_callback:
                await status_callback(msg)

        try:
            # 1. Capture audio
            await status("Listening...")
            if self._capture is None:
                return {"error": "No audio capture available"}
            wav_bytes = await self._capture.record_until_silence()

            # 2. Send to STT
            await status("Transcribing...")
            transcript = await self._transcribe(wav_bytes)
            if not transcript:
                await status("Didn't catch that.")
                return {"error": "Empty transcript"}
            await status(f'Heard: "{transcript}"')

            # 3. Build context (include camera frame if available)
            context = await self._build_context()

            # 4. Send to brain
            await status("Thinking...")
            brain_result = await self._think(transcript, context)
            reply = brain_result.get("reply", "")
            commands = brain_result.get("commands", [])
            await status(f'Emiglio: "{reply}"')

            # 5. Execute commands (movement)
            for cmd in commands:
                await self._execute_command(cmd)

            # 6. Speak the reply via TTS
            if reply and self._playback:
                await status("Speaking...")
                audio = await self._synthesize(reply)
                if audio:
                    await self._playback.play_wav(audio)

            await status("Ready")
            return {"transcript": transcript, "reply": reply, "commands": commands}

        except Exception as e:
            logger.error("Conversation error: %s", e, exc_info=True)
            await status("Error occurred")
            return {"error": str(e)}
        finally:
            self._busy = False

    async def handle_text_interaction(self, text: str, status_callback=None) -> dict:
        """Process a text input (typed, not spoken) through the brain.

        Skips STT, still does brain + TTS + commands.
        """
        if self._busy:
            return {"error": "Already processing"}
        self._busy = True

        async def status(msg: str):
            logger.info("Conversation: %s", msg)
            if status_callback:
                await status_callback(msg)

        try:
            context = await self._build_context()

            await status("Thinking...")
            brain_result = await self._think(text, context)
            reply = brain_result.get("reply", "")
            commands = brain_result.get("commands", [])
            await status(f'Emiglio: "{reply}"')

            for cmd in commands:
                await self._execute_command(cmd)

            if reply and self._playback:
                await status("Speaking...")
                audio = await self._synthesize(reply)
                if audio:
                    await self._playback.play_wav(audio)

            await status("Ready")
            return {"transcript": text, "reply": reply, "commands": commands}

        except Exception as e:
            logger.error("Conversation error: %s", e, exc_info=True)
            await status("Error occurred")
            return {"error": str(e)}
        finally:
            self._busy = False

    async def _transcribe(self, wav_bytes: bytes) -> str:
        """Call the STT server."""
        try:
            resp = await self._client.post(
                f"{settings.server_stt_url}/transcribe",
                files={"audio": ("audio.wav", wav_bytes, "audio/wav")},
            )
            resp.raise_for_status()
            return resp.json().get("text", "").strip()
        except Exception as e:
            logger.error("STT request failed: %s", e)
            return ""

    async def _think(self, transcript: str, context: str = "") -> dict:
        """Call the brain server."""
        try:
            resp = await self._client.post(
                f"{settings.server_brain_url}/think",
                json={"transcript": transcript, "context": context},
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("Brain request failed: %s", e)
            return {"reply": "Sorry, my brain isn't responding right now.", "commands": []}

    async def _synthesize(self, text: str) -> bytes | None:
        """Call the TTS server."""
        try:
            resp = await self._client.post(
                f"{settings.server_tts_url}/synthesize",
                json={"text": text},
            )
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            logger.error("TTS request failed: %s", e)
            return None

    async def _build_context(self) -> str:
        """Build context string, optionally including camera description."""
        if self._camera is None:
            return ""
        jpeg = self._camera.get_jpeg()
        if jpeg is None:
            return ""
        b64 = base64.b64encode(jpeg).decode()
        return f"[Camera frame available as base64 JPEG: {b64[:100]}... ({len(b64)} chars total)]"

    async def _execute_command(self, cmd: dict) -> None:
        """Execute a brain command by publishing to the event bus."""
        action = cmd.get("action", "")
        params = cmd.get("params", "")

        if action == "move":
            speeds = MOVE_PRESETS.get(params)
            if speeds:
                logger.info("Executing move: %s", params)
                await self._bus.publish(
                    Events.MOTOR_COMMAND,
                    MotorCommand(left=speeds[0], right=speeds[1]),
                )
                # Hold the movement briefly then stop
                if params != "stop":
                    await asyncio.sleep(MOVE_DURATION)
                    await self._bus.publish(
                        Events.MOTOR_COMMAND,
                        MotorCommand(left=0, right=0),
                    )
            else:
                logger.warning("Unknown move direction: %s", params)
        else:
            logger.warning("Unknown command action: %s", action)

    async def close(self) -> None:
        await self._client.aclose()
