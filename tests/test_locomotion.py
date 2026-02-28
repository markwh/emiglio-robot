"""Tests for locomotion subsystem."""

import pytest
from emiglio.event_bus import EventBus
from emiglio.models import Events, MotorCommand, JoystickInput
from emiglio.locomotion.controller import LocomotionController


async def test_joystick_forward():
    cmd = LocomotionController.joystick_to_motor(JoystickInput(x=0, y=1.0))
    assert cmd.left == pytest.approx(1.0)
    assert cmd.right == pytest.approx(1.0)


async def test_joystick_backward():
    cmd = LocomotionController.joystick_to_motor(JoystickInput(x=0, y=-1.0))
    assert cmd.left == pytest.approx(-1.0)
    assert cmd.right == pytest.approx(-1.0)


async def test_joystick_turn_right():
    cmd = LocomotionController.joystick_to_motor(JoystickInput(x=1.0, y=0))
    assert cmd.left == pytest.approx(1.0)
    assert cmd.right == pytest.approx(-1.0)


async def test_joystick_turn_left():
    cmd = LocomotionController.joystick_to_motor(JoystickInput(x=-1.0, y=0))
    assert cmd.left == pytest.approx(-1.0)
    assert cmd.right == pytest.approx(1.0)


async def test_joystick_center():
    cmd = LocomotionController.joystick_to_motor(JoystickInput(x=0, y=0))
    assert cmd.left == pytest.approx(0.0)
    assert cmd.right == pytest.approx(0.0)


async def test_joystick_diagonal_normalized():
    cmd = LocomotionController.joystick_to_motor(JoystickInput(x=1.0, y=1.0))
    # Should be normalized so max is 1.0
    assert abs(cmd.left) <= 1.0
    assert abs(cmd.right) <= 1.0
    assert cmd.left == pytest.approx(1.0)
    assert cmd.right == pytest.approx(0.0)


async def test_motor_command_clamping():
    cmd = MotorCommand(left=2.0, right=-3.0)
    assert cmd.left == 1.0
    assert cmd.right == -1.0


async def test_controller_handles_motor_command(bus: EventBus):
    controller = LocomotionController(bus)
    # Publishing a motor command should not raise in mock mode
    await bus.publish(Events.MOTOR_COMMAND, MotorCommand(left=0.5, right=0.5))
    controller.cleanup()
