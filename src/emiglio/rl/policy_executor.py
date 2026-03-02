"""Bridge between a trained SB3 RL policy and real-time motor execution.

Loads a PPO model, maintains an internal Simulator for position tracking,
and publishes MotorCommand events to the EventBus while navigating waypoints.

Supports two model formats:
  - "nav" (8D obs, 4 skills): trained with PatrolNavEnv from calibrate_patrol.py
  - "legacy" (6D obs, 8 skills): trained with EmiglioNavEnv
The format is auto-detected from the model's observation space shape.
"""

from __future__ import annotations

import asyncio
import logging
import math
from pathlib import Path
from typing import Any

import numpy as np

from emiglio.event_bus import EventBus
from emiglio.models import Events, MotorCommand
from emiglio.rl.sim import SIM_SIZE, Simulator, SimConfig
from emiglio.rl.skills import (
    SKILL_NAMES,
    NUM_SKILLS,
    MOVE_PRESETS,
    COMPOUND_BASE_SPEED,
)

logger = logging.getLogger(__name__)

# Match EmiglioNavEnv defaults
GOAL_RADIUS = 30.0
MAX_STEPS_PER_WAYPOINT = 30

# Default models directory at project root
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODELS_DIR = _PROJECT_ROOT / "models"

# Nav-format skill mapping (matches PatrolNavEnv / calibrate_patrol.py)
NAV_SKILLS = ["forward", "backward", "left", "right"]
NAV_NUM_SKILLS = len(NAV_SKILLS)


class PolicyExecutor:
    """Loads a trained PPO model and navigates waypoints in real time."""

    def __init__(
        self,
        bus: EventBus,
        models_dir: Path | None = None,
    ) -> None:
        self._bus = bus
        self._models_dir = models_dir or DEFAULT_MODELS_DIR
        self._model: Any = None  # PPO model (lazy-loaded to avoid hard SB3 dependency)
        self._sim = Simulator()
        self._nav_format = False  # True if model uses nav-format (8D obs, 4 skills)

    def load_model(self, model_name: str) -> bool:
        """Load a saved PPO model by name. Returns False if not found or SB3 unavailable."""
        model_path = self._models_dir / model_name / "model.zip"
        if not model_path.exists():
            logger.warning("Model file not found: %s", model_path)
            return False

        try:
            from stable_baselines3 import PPO
        except ImportError:
            logger.warning("stable-baselines3 not installed — RL nav unavailable")
            return False

        try:
            # SB3 wants path without .zip extension
            self._model = PPO.load(str(model_path.with_suffix("")), env=None)

            # Auto-detect model format from observation space
            obs_dim = self._model.observation_space.shape[0]
            if obs_dim == 8:
                self._nav_format = True
                logger.info("Loaded RL nav model (nav-format, 4 skills): %s", model_name)
            else:
                self._nav_format = False
                logger.info("Loaded RL nav model (legacy-format, 8 skills): %s", model_name)

            return True
        except Exception:
            logger.exception("Failed to load model: %s", model_name)
            self._model = None
            return False

    @property
    def available(self) -> bool:
        """True if a model has been successfully loaded."""
        return self._model is not None

    def _get_obs(self, goal: tuple[float, float]) -> np.ndarray:
        """Build observation vector matching the loaded model's format."""
        s = self._sim.state

        if self._nav_format:
            # Nav-format: 8D with relative bearing (matches PatrolNavEnv)
            dx = goal[0] - s.x
            dy = goal[1] - s.y
            dist = math.hypot(dx, dy)
            diag = math.hypot(SIM_SIZE, SIM_SIZE)
            goal_angle = math.atan2(dy, dx)
            rel_bearing = goal_angle - s.heading
            return np.array(
                [
                    s.x / SIM_SIZE * 2 - 1,
                    s.y / SIM_SIZE * 2 - 1,
                    math.sin(s.heading),
                    math.cos(s.heading),
                    dist / diag * 2 - 1,
                    math.sin(rel_bearing),
                    math.cos(rel_bearing),
                    1.0 if dist < 60 else -1.0,
                ],
                dtype=np.float32,
            )
        else:
            # Legacy format: 6D absolute positions (matches EmiglioNavEnv)
            return np.array(
                [
                    s.x / SIM_SIZE,
                    s.y / SIM_SIZE,
                    math.sin(s.heading),
                    math.cos(s.heading),
                    goal[0] / SIM_SIZE,
                    goal[1] / SIM_SIZE,
                ],
                dtype=np.float32,
            )

    def _decode_action(self, action: np.ndarray) -> tuple[str, int, float, float]:
        """Decode model action into (skill_name, full_skill_idx, speed, duration)."""
        if self._nav_format:
            nav_idx = min(int(action[0] * NAV_NUM_SKILLS), NAV_NUM_SKILLS - 1)
            skill_name = NAV_SKILLS[nav_idx]
            full_idx = SKILL_NAMES.index(skill_name)
        else:
            full_idx = min(int(action[0] * NUM_SKILLS), NUM_SKILLS - 1)
            skill_name = SKILL_NAMES[full_idx]

        speed = float(action[1])
        duration = float(action[2])
        return skill_name, full_idx, speed, duration

    async def navigate_waypoints(
        self,
        waypoints: list[tuple[float, float]],
        speed_factor: float = 1.0,
        timeout_per_wp: float = 5.0,
    ) -> bool:
        """Navigate through all waypoints in sequence. Returns True if all reached."""
        # Reset sim to center, facing up
        self._sim.reset(SimConfig())
        fmt = "nav" if self._nav_format else "legacy"
        logger.info(
            "PolicyExecutor: navigating %d waypoints (format=%s, speed_factor=%.2f, timeout=%.1f)",
            len(waypoints), fmt, speed_factor, timeout_per_wp,
        )

        all_reached = True
        for i, wp in enumerate(waypoints):
            reached = await self._navigate_to_waypoint(wp, speed_factor, timeout_per_wp)
            s = self._sim.state
            dist = math.hypot(s.x - wp[0], s.y - wp[1])
            logger.info(
                "  WP%d (%.0f,%.0f): %s (pos=%.0f,%.0f dist=%.1f)",
                i, wp[0], wp[1],
                "REACHED" if reached else "MISSED",
                s.x, s.y, dist,
            )
            if not reached:
                all_reached = False

        # Final stop
        await self._bus.publish(Events.MOTOR_COMMAND, MotorCommand(left=0, right=0))
        return all_reached

    async def _navigate_to_waypoint(
        self,
        goal: tuple[float, float],
        speed_factor: float,
        timeout: float,
    ) -> bool:
        """Use the policy to navigate to a single goal. Returns True if reached."""
        elapsed = 0.0
        for _ in range(MAX_STEPS_PER_WAYPOINT):
            if elapsed >= timeout:
                break

            # Check if already at goal
            s = self._sim.state
            dist = math.hypot(s.x - goal[0], s.y - goal[1])
            if dist <= GOAL_RADIUS:
                return True

            # Get action from policy
            obs = self._get_obs(goal)
            action, _ = self._model.predict(obs, deterministic=True)

            # Decode action using model-appropriate mapping
            skill_name, _, speed, duration = self._decode_action(action)
            speed *= speed_factor
            remaining = timeout - elapsed
            duration = min(duration, remaining)
            duration = max(0.05, duration)  # ensure positive

            logger.debug(
                "    step: skill=%s speed=%.2f dur=%.2f dist=%.1f",
                skill_name, speed, duration, dist,
            )

            await self._execute_skill_rt(skill_name, speed, duration)
            elapsed += duration

        # Final distance check
        s = self._sim.state
        return math.hypot(s.x - goal[0], s.y - goal[1]) <= GOAL_RADIUS

    async def _execute_skill_rt(
        self, skill_name: str, speed: float, duration: float,
    ) -> None:
        """Execute a single skill: publish motor command, advance sim, sleep."""
        speed = max(-1.0, min(1.0, speed))

        if skill_name in MOVE_PRESETS:
            base_l, base_r = MOVE_PRESETS[skill_name]
            left = max(-1.0, min(1.0, base_l * speed))
            right = max(-1.0, min(1.0, base_r * speed))
            await self._bus.publish(Events.MOTOR_COMMAND, MotorCommand(left=left, right=right))
            self._sim.set_motors(left, right)
            self._sim.run_for(duration)
            await asyncio.sleep(duration)

        elif skill_name == "spin":
            spd = max(-1.0, min(1.0, COMPOUND_BASE_SPEED * speed))
            await self._bus.publish(Events.MOTOR_COMMAND, MotorCommand(left=spd, right=-spd))
            self._sim.set_motors(spd, -spd)
            self._sim.run_for(duration)
            await asyncio.sleep(duration)

        elif skill_name == "wiggle":
            step = 0.2
            spd = max(-1.0, min(1.0, COMPOUND_BASE_SPEED * speed))
            elapsed = 0.0
            go_left = True
            while elapsed < duration:
                t = min(step, duration - elapsed)
                if go_left:
                    await self._bus.publish(Events.MOTOR_COMMAND, MotorCommand(left=-spd, right=spd))
                    self._sim.set_motors(-spd, spd)
                else:
                    await self._bus.publish(Events.MOTOR_COMMAND, MotorCommand(left=spd, right=-spd))
                    self._sim.set_motors(spd, -spd)
                self._sim.run_for(t)
                await asyncio.sleep(t)
                elapsed += t
                go_left = not go_left

        elif skill_name == "dance":
            quarter = duration / 4.0
            # forward
            await self._execute_skill_rt("forward", speed, quarter)
            # spin
            await self._execute_skill_rt("spin", speed, quarter)
            # wiggle
            await self._execute_skill_rt("wiggle", speed, quarter)
            # backward
            await self._execute_skill_rt("backward", speed, quarter)
