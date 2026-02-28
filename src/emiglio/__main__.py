"""Emiglio robot entry point. Wires subsystems and starts the web server."""

import asyncio
import logging
import signal

import uvicorn

from emiglio.config import settings
from emiglio.event_bus import EventBus
from emiglio.locomotion.controller import LocomotionController
from emiglio.vision.camera import Camera
from emiglio.conversation import ConversationManager
from emiglio.web.server import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("emiglio")


def main() -> None:
    logger.info("Starting Emiglio (hardware_mode=%s)", settings.hardware_mode)

    bus = EventBus()
    locomotion = LocomotionController(bus)

    camera = Camera()
    camera.start()

    # Audio subsystems — optional, may fail if no PortAudio/sounddevice
    audio_capture = None
    audio_playback = None
    try:
        from emiglio.audio.capture import AudioCapture
        from emiglio.audio.playback import AudioPlayback
        audio_capture = AudioCapture()
        audio_playback = AudioPlayback()
        logger.info("Audio subsystem initialized")
    except OSError as e:
        logger.warning("Audio subsystem unavailable: %s", e)

    conversation = ConversationManager(
        bus=bus,
        camera=camera,
        audio_capture=audio_capture,
        audio_playback=audio_playback,
    )

    app = create_app(bus, locomotion, camera=camera, conversation=conversation)

    def shutdown(sig, frame):
        logger.info("Shutting down...")
        camera.stop()
        locomotion.cleanup()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    uvicorn.run(
        app,
        host=settings.web_host,
        port=settings.web_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
