"""High-level locomotion controller. Translates events into motor commands."""

import logging
from emiglio.event_bus import EventBus
from emiglio.models import Events, MotorCommand, JoystickInput
from emiglio.locomotion.driver import MotorDriver

logger = logging.getLogger(__name__)


class LocomotionController:
    """Subscribes to motor commands from the event bus and drives the motors."""

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._driver = MotorDriver()
        bus.subscribe(Events.MOTOR_COMMAND, self._on_motor_command)

    async def _on_motor_command(self, command: MotorCommand) -> None:
        self._driver.set_motors(command.left, command.right)

    @staticmethod
    def joystick_to_motor(joy: JoystickInput) -> MotorCommand:
        """Convert joystick x/y to differential drive motor speeds.

        Uses arcade-drive mixing:
        - y controls forward/backward thrust
        - x controls turning by reducing one side
        """
        left = joy.y + joy.x
        right = joy.y - joy.x
        # Normalize so neither exceeds [-1, 1]
        max_val = max(abs(left), abs(right), 1.0)
        return MotorCommand(left=left / max_val, right=right / max_val)

    def stop(self) -> None:
        self._driver.stop()

    def cleanup(self) -> None:
        self._driver.cleanup()
