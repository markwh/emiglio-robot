"""Low-level motor driver wrapping gpiozero for TB6612FNG motor board."""

import logging
from emiglio.config import settings

logger = logging.getLogger(__name__)


class MotorDriver:
    """Drives two DC motors via TB6612FNG connected to Pi GPIO.

    In mock mode, logs commands instead of driving real pins.
    Each motor takes a speed in [-1.0, 1.0] where negative is backward.
    """

    def __init__(self) -> None:
        self._mock = settings.hardware_mode == "mock"
        if self._mock:
            logger.info("MotorDriver running in MOCK mode")
            self._left = None
            self._right = None
        else:
            from gpiozero import Motor
            self._left = Motor(
                forward=settings.motor_left_forward,
                backward=settings.motor_left_backward,
                enable=settings.motor_left_enable,
            )
            self._right = Motor(
                forward=settings.motor_right_forward,
                backward=settings.motor_right_backward,
                enable=settings.motor_right_enable,
            )
            logger.info("MotorDriver initialized with real GPIO pins")

    def set_motors(self, left: float, right: float) -> None:
        """Set motor speeds. Values clamped to [-1.0, 1.0]."""
        left = max(-1.0, min(1.0, left))
        right = max(-1.0, min(1.0, right))

        if self._mock:
            logger.info("MOCK motors: left=%.2f, right=%.2f", left, right)
            return

        self._drive_motor(self._left, left)
        self._drive_motor(self._right, right)

    def stop(self) -> None:
        """Stop both motors."""
        if self._mock:
            logger.info("MOCK motors: STOP")
            return
        self._left.stop()
        self._right.stop()

    def _drive_motor(self, motor, speed: float) -> None:
        if speed > 0:
            motor.forward(speed)
        elif speed < 0:
            motor.backward(abs(speed))
        else:
            motor.stop()

    def cleanup(self) -> None:
        """Release GPIO resources."""
        self.stop()
        if not self._mock:
            self._left.close()
            self._right.close()
        logger.info("MotorDriver cleaned up")
