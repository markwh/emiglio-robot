"""Python port of the JS differential-drive robot simulator.

Physics constants match app.js lines 57-108 exactly so that Python RL training
produces trajectories visually identical to the browser canvas.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

SIM_SIZE = 500
ROBOT_RADIUS = 14
MAX_SPEED = 130  # px/s at motor=1.0
TURN_RATE = 3.5  # rad/s at full differential
WHEELBASE = 0.5
MARGIN = ROBOT_RADIUS + 3


@dataclass
class SimConfig:
    """Per-episode physics parameters for domain randomization."""
    max_speed: float = MAX_SPEED
    turn_rate: float = TURN_RATE
    motor_noise_std: float = 0.0
    start_x: float = SIM_SIZE / 2
    start_y: float = SIM_SIZE / 2
    start_heading: float = -math.pi / 2


def randomized_config(rng: random.Random, strength: float) -> SimConfig:
    """Create a SimConfig with randomized physics scaled by *strength* (0-1)."""
    speed_factor = max(0.5, 1.0 + rng.gauss(0, 0.15 * strength))
    turn_factor = max(0.5, 1.0 + rng.gauss(0, 0.15 * strength))
    return SimConfig(
        max_speed=MAX_SPEED * speed_factor,
        turn_rate=TURN_RATE * turn_factor,
        motor_noise_std=0.05 * strength,
        start_x=SIM_SIZE / 2 + rng.uniform(-30, 30) * strength,
        start_y=SIM_SIZE / 2 + rng.uniform(-30, 30) * strength,
        start_heading=-math.pi / 2 + rng.gauss(0, 0.2 * strength),
    )


@dataclass
class RobotState:
    x: float = SIM_SIZE / 2
    y: float = SIM_SIZE / 2
    heading: float = -math.pi / 2  # facing up
    motor_left: float = 0.0
    motor_right: float = 0.0


class Simulator:
    """Lightweight 2-D differential-drive physics sim."""

    def __init__(self, config: SimConfig | None = None) -> None:
        self.config = config or SimConfig()
        self.state = RobotState(
            x=self.config.start_x,
            y=self.config.start_y,
            heading=self.config.start_heading,
        )
        self.wall_contact = False
        self._rng = random.Random()

    def reset(self, config: SimConfig | None = None) -> RobotState:
        if config is not None:
            self.config = config
        self.state = RobotState(
            x=self.config.start_x,
            y=self.config.start_y,
            heading=self.config.start_heading,
        )
        self.wall_contact = False
        return self.state

    def set_motors(self, left: float, right: float) -> None:
        self.state.motor_left = max(-1.0, min(1.0, left))
        self.state.motor_right = max(-1.0, min(1.0, right))

    def step(self, dt: float) -> RobotState:
        s = self.state
        ml, mr = s.motor_left, s.motor_right

        # Apply motor noise (to effective values, not stored state)
        if self.config.motor_noise_std > 0:
            ml += self._rng.gauss(0, self.config.motor_noise_std)
            mr += self._rng.gauss(0, self.config.motor_noise_std)
            ml = max(-1.0, min(1.0, ml))
            mr = max(-1.0, min(1.0, mr))

        v = ((ml + mr) / 2) * self.config.max_speed
        omega = ((ml - mr) / WHEELBASE) * self.config.turn_rate

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
