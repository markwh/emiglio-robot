"""Tests for the RL simulator, skill executor, and Gymnasium environment."""

import math
import random

import numpy as np
import pytest

from emiglio.rl.sim import (
    SIM_SIZE, MARGIN, MAX_SPEED, TURN_RATE, WHEELBASE,
    Simulator, SimConfig, randomized_config,
)
from emiglio.rl.skills import SKILL_NAMES, NUM_SKILLS, execute_skill
from emiglio.rl.env import EmiglioNavEnv


# ========== Simulator tests ==========


class TestSimulator:
    def test_reset_position(self):
        sim = Simulator()
        state = sim.reset()
        assert state.x == SIM_SIZE / 2
        assert state.y == SIM_SIZE / 2
        assert state.heading == pytest.approx(-math.pi / 2)

    def test_forward_motion(self):
        """Robot facing up (-pi/2) with both motors forward → y decreases."""
        sim = Simulator()
        sim.reset()
        sim.set_motors(1.0, 1.0)
        sim.step(0.1)
        assert sim.state.y < SIM_SIZE / 2

    def test_spin_in_place(self):
        """Equal and opposite motors → heading changes, position barely moves."""
        sim = Simulator()
        sim.reset()
        start_x, start_y = sim.state.x, sim.state.y
        start_heading = sim.state.heading
        sim.set_motors(0.5, -0.5)
        sim.step(0.1)
        # Heading must change
        assert sim.state.heading != pytest.approx(start_heading)
        # Position should remain close to center (no linear velocity)
        assert abs(sim.state.x - start_x) < 0.01
        assert abs(sim.state.y - start_y) < 0.01

    def test_wall_clamping(self):
        """Robot can't leave the arena."""
        sim = Simulator()
        sim.reset()
        sim.set_motors(1.0, 1.0)
        # Run for a long time — should hit the wall
        sim.run_for(10.0, dt=0.02)
        assert sim.state.x >= MARGIN
        assert sim.state.x <= SIM_SIZE - MARGIN
        assert sim.state.y >= MARGIN
        assert sim.state.y <= SIM_SIZE - MARGIN
        assert sim.wall_contact

    def test_physics_match_js(self):
        """Manual calculation matches step() output."""
        sim = Simulator()
        sim.reset()
        sim.set_motors(0.6, 0.3)
        dt = 0.05
        # Manually compute expected values
        ml, mr = 0.6, 0.3
        v = ((ml + mr) / 2) * MAX_SPEED
        omega = ((ml - mr) / WHEELBASE) * TURN_RATE
        expected_heading = -math.pi / 2 + omega * dt
        expected_x = SIM_SIZE / 2 + v * math.cos(-math.pi / 2) * dt
        expected_y = SIM_SIZE / 2 + v * math.sin(-math.pi / 2) * dt
        # Note: heading updates first in the code, but position uses the NEW heading
        # Actually re-read: heading updates, then position uses updated heading
        heading_new = -math.pi / 2 + omega * dt
        expected_x = SIM_SIZE / 2 + v * math.cos(heading_new) * dt
        expected_y = SIM_SIZE / 2 + v * math.sin(heading_new) * dt

        sim.step(dt)
        assert sim.state.heading == pytest.approx(heading_new)
        assert sim.state.x == pytest.approx(expected_x, abs=0.01)
        assert sim.state.y == pytest.approx(expected_y, abs=0.01)


# ========== Skills tests ==========


class TestSkills:
    def test_forward_skill_moves_robot(self):
        """Forward skill with speed=1 → y decreases (heading is up)."""
        sim = Simulator()
        sim.reset()
        execute_skill(sim, 0, 1.0, 0.5)  # forward
        assert sim.state.y < SIM_SIZE / 2

    def test_stop_skill(self):
        """Stop skill → no movement."""
        sim = Simulator()
        sim.reset()
        start_x, start_y = sim.state.x, sim.state.y
        execute_skill(sim, 4, 1.0, 0.5)  # stop
        assert sim.state.x == pytest.approx(start_x)
        assert sim.state.y == pytest.approx(start_y)

    def test_clamp_params(self):
        """Out-of-range values get clamped, no errors."""
        sim = Simulator()
        sim.reset()
        # Speed too high, duration too long — should clamp
        traj = execute_skill(sim, 0, 5.0, 100.0)
        assert len(traj) > 0

    def test_all_skills_execute(self):
        """All 8 skills run without error."""
        for idx in range(NUM_SKILLS):
            sim = Simulator()
            sim.reset()
            traj = execute_skill(sim, idx, 0.5, 0.3)
            assert isinstance(traj, list)

    def test_trajectory_returned(self):
        """Execute skill returns a non-empty trajectory for movement skills."""
        sim = Simulator()
        sim.reset()
        traj = execute_skill(sim, 0, 1.0, 1.0)  # forward
        assert len(traj) > 0
        assert len(traj[0]) == 3  # (x, y, heading)


# ========== Environment tests ==========


class TestEnvironment:
    def test_observation_shape(self):
        env = EmiglioNavEnv()
        obs, info = env.reset(seed=42)
        assert obs.shape == (6,)
        assert obs.dtype == np.float32

    def test_step_returns_correct_shapes(self):
        env = EmiglioNavEnv()
        env.reset(seed=42)
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)
        assert obs.shape == (6,)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    def test_episode_terminates_on_max_steps(self):
        env = EmiglioNavEnv(max_steps=5)
        env.reset(seed=42)
        # Use stop action to not reach goal
        stop_action = np.array([4.0 / 8, 0.5, 0.5], dtype=np.float32)
        for i in range(5):
            obs, reward, terminated, truncated, info = env.step(stop_action)
            if terminated or truncated:
                break
        assert truncated or terminated

    def test_goal_far_from_center(self):
        env = EmiglioNavEnv(min_goal_dist=100.0)
        env.reset(seed=42)
        center = SIM_SIZE / 2
        dist = math.hypot(env.goal_x - center, env.goal_y - center)
        assert dist >= 100.0

    def test_custom_reward_fn(self):
        """Pluggable reward function is called."""
        calls = []

        def custom_reward(prev_dist, curr_dist, wall_contact, duration, env):
            calls.append(1)
            return 42.0

        env = EmiglioNavEnv(reward_fn=custom_reward)
        env.reset(seed=42)
        action = env.action_space.sample()
        obs, reward, _, _, _ = env.step(action)
        assert len(calls) == 1
        # Reward should be 42.0 (no goal bonus since likely not reached)
        assert reward >= 42.0  # could be 52 if goal reached

    def test_info_on_terminal(self):
        """Terminal step includes trajectory and goal info."""
        env = EmiglioNavEnv(max_steps=1)
        env.reset(seed=42)
        action = env.action_space.sample()
        _, _, _, _, info = env.step(action)
        assert "episode_trajectory" in info
        assert "episode_goal" in info
        assert "episode_reward" in info

    def test_observation_values_normalized(self):
        """All observation values should be in reasonable range."""
        env = EmiglioNavEnv()
        obs, _ = env.reset(seed=42)
        # x/size, y/size, sin, cos, gx/size, gy/size
        assert 0.0 <= obs[0] <= 1.0  # x normalized
        assert 0.0 <= obs[1] <= 1.0  # y normalized
        assert -1.0 <= obs[2] <= 1.0  # sin
        assert -1.0 <= obs[3] <= 1.0  # cos
        assert 0.0 <= obs[4] <= 1.0  # goal x normalized
        assert 0.0 <= obs[5] <= 1.0  # goal y normalized


# ========== SimConfig and Domain Randomization tests ==========


class TestSimConfig:
    def test_default_config_matches_constants(self):
        """SimConfig defaults should match module-level constants."""
        cfg = SimConfig()
        assert cfg.max_speed == MAX_SPEED
        assert cfg.turn_rate == TURN_RATE
        assert cfg.motor_noise_std == 0.0
        assert cfg.start_x == SIM_SIZE / 2
        assert cfg.start_y == SIM_SIZE / 2
        assert cfg.start_heading == pytest.approx(-math.pi / 2)

    def test_randomized_config_varies(self):
        """strength=1.0 produces configs that differ from defaults."""
        rng = random.Random(42)
        configs = [randomized_config(rng, 1.0) for _ in range(20)]
        speeds = [c.max_speed for c in configs]
        # With 20 samples at strength 1.0, we should see variation
        assert max(speeds) != min(speeds)
        # Motor noise should be nonzero
        assert all(c.motor_noise_std > 0 for c in configs)

    def test_zero_strength_is_deterministic(self):
        """strength=0.0 produces a config identical to defaults."""
        rng = random.Random(42)
        cfg = randomized_config(rng, 0.0)
        assert cfg.max_speed == pytest.approx(MAX_SPEED)
        assert cfg.turn_rate == pytest.approx(TURN_RATE)
        assert cfg.motor_noise_std == 0.0
        assert cfg.start_x == pytest.approx(SIM_SIZE / 2)
        assert cfg.start_y == pytest.approx(SIM_SIZE / 2)
        assert cfg.start_heading == pytest.approx(-math.pi / 2)


class TestNoisySimulator:
    def test_noisy_step_runs(self):
        """Simulator with motor noise runs without error."""
        cfg = SimConfig(motor_noise_std=0.1)
        sim = Simulator(cfg)
        sim.set_motors(0.5, 0.5)
        for _ in range(100):
            sim.step(0.02)
        # Should still be within arena bounds
        assert sim.state.x >= MARGIN
        assert sim.state.x <= SIM_SIZE - MARGIN

    def test_config_reset(self):
        """Resetting with a new config applies the new config."""
        cfg1 = SimConfig(start_x=100, start_y=100)
        sim = Simulator(cfg1)
        assert sim.state.x == 100
        cfg2 = SimConfig(start_x=400, start_y=400)
        sim.reset(cfg2)
        assert sim.state.x == 400
        assert sim.state.y == 400


class TestEnvRandomization:
    def test_env_with_randomization(self):
        """EmiglioNavEnv with randomization_strength=0.5 produces nonzero motor noise."""
        env = EmiglioNavEnv(randomization_strength=0.5)
        env.reset(seed=42)
        # After reset, the sim should have a config with motor noise
        assert env.sim.config.motor_noise_std > 0

    def test_env_without_randomization(self):
        """Default env has zero motor noise."""
        env = EmiglioNavEnv()
        env.reset(seed=42)
        assert env.sim.config.motor_noise_std == 0.0
