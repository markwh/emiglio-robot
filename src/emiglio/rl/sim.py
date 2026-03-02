"""Python port of the JS differential-drive robot simulator.

Physics constants match app.js lines 57-108 exactly so that Python RL training
produces trajectories visually identical to the browser canvas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

SIM_SIZE = 500
ROBOT_RADIUS = 14
MAX_SPEED = 130  # px/s at motor=1.0
TURN_RATE = 3.5  # rad/s at full differential
WHEELBASE = 0.5
MARGIN = ROBOT_RADIUS + 3


@dataclass
class RobotState:
    x: float = SIM_SIZE / 2
    y: float = SIM_SIZE / 2
    heading: float = -math.pi / 2  # facing up
    motor_left: float = 0.0
    motor_right: float = 0.0


class Simulator:
    """Lightweight 2-D differential-drive physics sim."""

    def __init__(self) -> None:
        self.state = RobotState()
        self.wall_contact = False

    def reset(self) -> RobotState:
        self.state = RobotState()
        self.wall_contact = False
        return self.state

    def set_motors(self, left: float, right: float) -> None:
        self.state.motor_left = max(-1.0, min(1.0, left))
        self.state.motor_right = max(-1.0, min(1.0, right))

    def step(self, dt: float) -> RobotState:
        s = self.state
        ml, mr = s.motor_left, s.motor_right

        v = ((ml + mr) / 2) * MAX_SPEED
        omega = ((ml - mr) / WHEELBASE) * TURN_RATE

        s.heading += omega * dt
        s.x += v * math.cos(s.heading) * dt
        s.y += v * math.sin(s.heading) * dt

        # Clamp to arena
        self.wall_contact = False
        if s.x < MARGIN:
            s.x = MARGIN
            self.wall_contact = True
        elif s.x > SIM_SIZE - MARGIN:
            s.x = SIM_SIZE - MARGIN
            self.wall_contact = True
        if s.y < MARGIN:
            s.y = MARGIN
            self.wall_contact = True
        elif s.y > SIM_SIZE - MARGIN:
            s.y = SIM_SIZE - MARGIN
            self.wall_contact = True

        return s

    def run_for(self, duration: float, dt: float = 0.02) -> list[tuple[float, float, float]]:
        """Run physics for *duration* seconds, returning trajectory as [(x, y, heading), ...]."""
        trajectory: list[tuple[float, float, float]] = []
        elapsed = 0.0
        while elapsed < duration:
            t = min(dt, duration - elapsed)
            self.step(t)
            trajectory.append((self.state.x, self.state.y, self.state.heading))
            elapsed += t
        return trajectory
