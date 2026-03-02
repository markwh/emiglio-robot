"""Navigation-focused Gymnasium environment for geometry-based skill training.

Uses only 4 directional skills (forward, backward, left, right) and an 8D
observation that includes relative bearing to the goal.  This learns waypoint
navigation much faster than the legacy 8-skill EmiglioNavEnv.

Observation (Box, 8D):
    [x_norm, y_norm, sin(heading), cos(heading),
     dist_norm, sin(relative_bearing), cos(relative_bearing),
     proximity_flag]

Action (Box, 3D):
    [skill_selector (0-1 -> 4 skills), speed (0.2-1.0), duration (0.2-2.0)]
"""

from __future__ import annotations

import math

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from emiglio.rl.sim import SIM_SIZE, MARGIN, Simulator, SimConfig
from emiglio.rl.skills import SKILL_NAMES, execute_skill

# Only skills useful for waypoint navigation
NAV_SKILLS = ["forward", "backward", "left", "right"]
NAV_NUM_SKILLS = len(NAV_SKILLS)

# Map nav skill index -> full skill index for execute_skill()
_NAV_TO_FULL = [SKILL_NAMES.index(s) for s in NAV_SKILLS]


class PatrolNavEnv(gym.Env):
    """Simplified navigation env for geometry-based skill training.

    Key differences from EmiglioNavEnv:
      - 4 nav-only skills (forward, backward, left, right) instead of 8
      - Observation includes relative bearing and normalized distance
      - Stronger approach reward with proximity bonus
      - Episode trajectory recording for UI replay
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        max_steps: int = 40,
        goal_radius: float = 30.0,
        min_goal_dist: float = 50.0,
    ) -> None:
        super().__init__()
        self.max_steps = max_steps
        self.goal_radius = goal_radius
        self.min_goal_dist = min_goal_dist
        self._diag = math.hypot(SIM_SIZE, SIM_SIZE)

        self.sim = Simulator()
        self.goal_x = 0.0
        self.goal_y = 0.0
        self._step_count = 0
        self._episode_reward = 0.0
        self.episode_trajectory: list[tuple[float, float, float]] = []
        self._skill_counts: list[int] = [0] * NAV_NUM_SKILLS
        self._wall_hits = 0

        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(8,), dtype=np.float32,
        )

        self.action_space = spaces.Box(
            low=np.array([0.0, 0.2, 0.2], dtype=np.float32),
            high=np.array([1.0, 1.0, 2.0], dtype=np.float32),
        )

    def _get_obs(self) -> np.ndarray:
        s = self.sim.state
        dx = self.goal_x - s.x
        dy = self.goal_y - s.y
        dist = math.hypot(dx, dy)
        goal_angle = math.atan2(dy, dx)
        rel_bearing = goal_angle - s.heading
        return np.array([
            s.x / SIM_SIZE * 2 - 1,
            s.y / SIM_SIZE * 2 - 1,
            math.sin(s.heading),
            math.cos(s.heading),
            dist / self._diag * 2 - 1,
            math.sin(rel_bearing),
            math.cos(rel_bearing),
            1.0 if dist < 60 else -1.0,
        ], dtype=np.float32)

    def _dist_to_goal(self) -> float:
        s = self.sim.state
        return math.hypot(s.x - self.goal_x, s.y - self.goal_y)

    def _place_goal(self) -> None:
        center = SIM_SIZE / 2
        for _ in range(100):
            gx = self.np_random.uniform(MARGIN + 10, SIM_SIZE - MARGIN - 10)
            gy = self.np_random.uniform(MARGIN + 10, SIM_SIZE - MARGIN - 10)
            if math.hypot(gx - center, gy - center) >= self.min_goal_dist:
                self.goal_x, self.goal_y = gx, gy
                return
        self.goal_x = SIM_SIZE - 50
        self.goal_y = SIM_SIZE - 50

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed, options=options)
        self.sim.reset()
        self._place_goal()
        self._step_count = 0
        self._episode_reward = 0.0
        self._skill_counts = [0] * NAV_NUM_SKILLS
        self._wall_hits = 0

        s = self.sim.state
        self.episode_trajectory = [(s.x, s.y, s.heading)]
        return self._get_obs(), {}

    def step(self, action):
        nav_idx = min(int(action[0] * NAV_NUM_SKILLS), NAV_NUM_SKILLS - 1)
        full_idx = _NAV_TO_FULL[nav_idx]
        speed = float(action[1])
        duration = float(action[2])

        self._skill_counts[nav_idx] += 1

        prev_dist = self._dist_to_goal()
        execute_skill(self.sim, full_idx, speed, duration)
        self._step_count += 1
        curr_dist = self._dist_to_goal()

        if self.sim.wall_contact:
            self._wall_hits += 1

        # Record trajectory
        s = self.sim.state
        self.episode_trajectory.append((s.x, s.y, s.heading))

        # -- Reward --
        reward = (prev_dist - curr_dist) * 0.05  # strong approach bonus
        if self.sim.wall_contact:
            reward -= 0.1
        if curr_dist < 60:
            reward += 0.15 * (60 - curr_dist) / 60  # proximity bonus
        reward -= 0.003 * duration  # minimal time penalty

        goal_reached = curr_dist <= self.goal_radius
        if goal_reached:
            reward += 10.0

        self._episode_reward += reward
        terminated = goal_reached
        truncated = self._step_count >= self.max_steps

        info = {}
        if terminated or truncated:
            info["goal_reached"] = goal_reached
            info["dist_to_goal"] = curr_dist
            info["episode_reward"] = self._episode_reward
            info["episode_trajectory"] = list(self.episode_trajectory)
            info["episode_goal"] = (self.goal_x, self.goal_y)
            info["skill_counts"] = list(self._skill_counts)
            info["wall_hits"] = self._wall_hits

        return self._get_obs(), reward, terminated, truncated, info
