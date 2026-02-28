"""FastAPI web server with WebSocket for real-time robot control."""

import json
import logging
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from emiglio.event_bus import EventBus
from emiglio.models import Events, MotorCommand, JoystickInput
from emiglio.locomotion.controller import LocomotionController

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).parent / "static"


def create_app(bus: EventBus, locomotion: LocomotionController) -> FastAPI:
    app = FastAPI(title="Emiglio Robot")

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/")
    async def index():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health")
    async def health():
        return {"status": "ok"}

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
                else:
                    logger.warning("Unknown WebSocket message type: %s", msg_type)
        except WebSocketDisconnect:
            logger.info("WebSocket client disconnected")
            await bus.publish(Events.MOTOR_COMMAND, MotorCommand(0, 0))

    return app
