"""Gymnasium environment for Emiglio goal-navigation RL training."""

from __future__ import annotations

import math
import random
from typing import Any, Callable

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from emiglio.rl.sim import SIM_SIZE, Simulator, randomized_config
from emiglio.rl.skills import NUM_SKILLS, SKILL_NAMES, execute_skill

# Default reward function type
RewardFn = Callable[
    [float, float, bool, float, "EmiglioNavEnv"],  # prev_dist, curr_dist, wall_contact, duration, env
    float,
]


def default_reward_fn(
    prev_dist: float,
    curr_dist: float,
    wall_contact: bool,
    duration: float,
    env: "EmiglioNavEnv",
) -> float:
    reward = (prev_dist - curr_dist) * 0.01  # approach bonus
    if wall_contact:
        reward -= 0.5
    reward -= 0.01 * duration  # time penalty
    return reward


class EmiglioNavEnv(gym.Env):
    """Navigate to a randomly placed goal using parameterized movement skills.

    Observation (Box, 6D):
        [x/size, y/size, sin(heading), cos(heading), goal_x/size, goal_y/size]

    Action (Box, 3D):
        [skill_selector (0-1 → index), speed (0.1-1.0), duration (0.1-5.0)]
    """

    metadata = {"render_modes": []}

    def __init__(
        self,
        max_steps: int = 50,
        max_sim_time: float = 120.0,
        goal_radius: float = 30.0,
        min_goal_dist: float = 100.0,
        reward_fn: RewardFn | None = None,
        sim_dt: float = 0.02,
        randomization_strength: float = 0.0,
    ) -> None:
        super().__init__()

        self.max_steps = max_steps
        self.max_sim_time = max_sim_time
        self.goal_radius = goal_radius
        self.min_goal_dist = min_goal_dist
        self.reward_fn = reward_fn or default_reward_fn
        self.sim_dt = sim_dt
        self.randomization_strength = randomization_strength
        self._domain_rng = random.Random()

        self.sim = Simulator()
        self.goal_x = 0.0
        self.goal_y = 0.0
        self._step_count = 0
        self._sim_time = 0.0
        self._episode_reward = 0.0
        self.episode_trajectory: list[tuple[float, float, float]] = []
        self._skill_counts: list[int] = [0] * NUM_SKILLS  # per-episode skill usage
        self._wall_hits = 0

        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(6,), dtype=np.float32,
        )

        # skill_selector [0,1], speed [0.1,1.0], duration [0.1,5.0]
        self.action_space = spaces.Box(
            low=np.array([0.0, 0.1, 0.1], dtype=np.float32),
            high=np.array([1.0, 1.0, 5.0], dtype=np.float32),
        )

    def _get_obs(self) -> np.ndarray:
        s = self.sim.state
        return np.array([
            s.x / SIM_SIZE,
            s.y / SIM_SIZE,
            math.sin(s.heading),
            math.cos(s.heading),
            self.goal_x / SIM_SIZE,
            self.goal_y / SIM_SIZE,
        ], dtype=np.float32)

    def _dist_to_goal(self) -> float:
        s = self.sim.state
        return math.hypot(s.x - self.goal_x, s.y - self.goal_y)

    def _place_goal(self, np_random: np.random.Generator) -> None:
        center = SIM_SIZE / 2
        for _ in range(100):
            gx = np_random.uniform(30, SIM_SIZE - 30)
            gy = np_random.uniform(30, SIM_SIZE - 30)
            if math.hypot(gx - center, gy - center) >= self.min_goal_dist:
                self.goal_x, self.goal_y = gx, gy
                return
        # Fallback: place at edge
        self.goal_x = SIM_SIZE - 50
        self.goal_y = SIM_SIZE - 50

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed, options=options)
        if self.randomization_strength > 0:
            cfg = randomized_config(self._domain_rng, self.randomization_strength)
            self.sim.reset(cfg)
        else:
            self.sim.reset()
        self._place_goal(self.np_random)
        self._step_count = 0
        self._sim_time = 0.0
        self._episode_reward = 0.0
        self._skill_counts = [0] * NUM_SKILLS
        self._wall_hits = 0
        self.episode_trajectory = [(self.sim.state.x, self.sim.state.y, self.sim.state.heading)]
        return self._get_obs(), {}

    def step(self, action: np.ndarray) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        skill_index = min(int(action[0] * NUM_SKILLS), NUM_SKILLS - 1)
        speed = float(action[1])
        duration = float(action[2])

        self._skill_counts[skill_index] += 1

        prev_dist = self._dist_to_goal()

        traj = execute_skill(self.sim, skill_index, speed, duration, self.sim_dt)
        self.episode_trajectory.extend(traj)
        self._sim_time += duration
        self._step_count += 1

        curr_dist = self._dist_to_goal()
        if self.sim.wall_contact:
            self._wall_hits += 1
        goal_reached = curr_dist <= self.goal_radius

        reward = self.reward_fn(prev_dist, curr_dist, self.sim.wall_contact, duration, self)
        if goal_reached:
            reward += 10.0
        self._episode_reward += reward

        terminated = goal_reached
        truncated = self._step_count >= self.max_steps or self._sim_time >= self.max_sim_time

        info: dict[str, Any] = {}
        if terminated or truncated:
            info["episode_trajectory"] = list(self.episode_trajectory)
            info["episode_goal"] = (self.goal_x, self.goal_y)
            info["episode_reward"] = self._episode_reward
            info["goal_reached"] = goal_reached
            info["dist_to_goal"] = curr_dist
            # Diagnostic: per-episode skill distribution and wall hits
            info["skill_counts"] = list(self._skill_counts)
            info["wall_hits"] = self._wall_hits

        return self._get_obs(), reward, terminated, truncated, info
