"""Emiglio robot entry point. Wires subsystems and starts the web server."""

import asyncio
import logging
import signal

import uvicorn

from emiglio.config import settings
from emiglio.event_bus import EventBus
from emiglio.locomotion.controller import LocomotionController
from emiglio.vision.camera import Camera
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

    app = create_app(bus, locomotion, camera=camera)

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
