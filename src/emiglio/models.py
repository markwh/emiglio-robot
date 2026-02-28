"""Shared event and command models."""

from dataclasses import dataclass


# -- Event types (string constants) --
class Events:
    MOTOR_COMMAND = "motor.command"
    MOTOR_STATUS = "motor.status"
    VOICE_INPUT = "voice.input"
    VOICE_OUTPUT = "voice.output"
    BRAIN_COMMAND = "brain.command"
    CAMERA_FRAME = "camera.frame"


# -- Data models --
@dataclass
class MotorCommand:
    """Command to set motor speeds. Values in [-1.0, 1.0]."""
    left: float
    right: float

    def __post_init__(self) -> None:
        self.left = max(-1.0, min(1.0, self.left))
        self.right = max(-1.0, min(1.0, self.right))


@dataclass
class JoystickInput:
    """Raw joystick input from web UI. x=[-1,1] (left/right), y=[-1,1] (back/forward)."""
    x: float
    y: float
