"""Tests for the PolicyExecutor (RL policy → real-time motor commands)."""

import math

import numpy as np
import pytest
from unittest.mock import MagicMock

from emiglio.event_bus import EventBus
from emiglio.models import Events, MotorCommand
from emiglio.rl.policy_executor import (
    PolicyExecutor, GOAL_RADIUS, MAX_STEPS_PER_WAYPOINT,
    NAV_SKILLS, NAV_NUM_SKILLS,
)
from emiglio.rl.sim import SIM_SIZE, Simulator


def _make_mock_model(action_fn=None):
    """Create a mock SB3 model with a predict() method."""
    model = MagicMock()
    if action_fn is None:
        # Default: always predict "forward" at speed 0.5, duration 0.3
        def action_fn(obs, deterministic=True):
            return np.array([0.0, 0.5, 0.3], dtype=np.float32), None
    model.predict = MagicMock(side_effect=action_fn)
    return model


class TestAvailability:
    def test_available_false_before_load(self, bus: EventBus):
        pe = PolicyExecutor(bus=bus)
        assert not pe.available

    def test_load_model_missing(self, bus: EventBus, tmp_path):
        pe = PolicyExecutor(bus=bus, models_dir=tmp_path)
        assert not pe.load_model("nonexistent_model")
        assert not pe.available


class TestObservation:
    def test_observation_shape_and_range(self, bus: EventBus):
        pe = PolicyExecutor(bus=bus)
        obs = pe._get_obs((400.0, 100.0))
        assert obs.shape == (6,)
        assert obs.dtype == np.float32
        # Normalized positions should be in [0, 1]
        assert 0.0 <= obs[0] <= 1.0
        assert 0.0 <= obs[1] <= 1.0
        # sin/cos should be in [-1, 1]
        assert -1.0 <= obs[2] <= 1.0
        assert -1.0 <= obs[3] <= 1.0

    def test_observation_matches_env(self, bus: EventBus):
        """_get_obs() should produce the same values as EmiglioNavEnv._get_obs()."""
        from emiglio.rl.env import EmiglioNavEnv

        env = EmiglioNavEnv()
        env.reset(seed=42)

        pe = PolicyExecutor(bus=bus)
        # Sync PE sim state to match env state
        pe._sim.state.x = env.sim.state.x
        pe._sim.state.y = env.sim.state.y
        pe._sim.state.heading = env.sim.state.heading

        goal = (env.goal_x, env.goal_y)
        pe_obs = pe._get_obs(goal)
        env_obs = env._get_obs()

        np.testing.assert_array_almost_equal(pe_obs, env_obs)


class TestNavigation:
    async def test_navigate_single_waypoint(self, bus: EventBus):
        """Mock model always predicts 'forward' — should approach a waypoint ahead."""
        pe = PolicyExecutor(bus=bus)
        pe._model = _make_mock_model()

        # Waypoint directly ahead (robot faces up = -y)
        center = SIM_SIZE / 2
        target = (center, center - 60)

        result = await pe.navigate_waypoints([target], timeout_per_wp=5.0)
        # Should have called predict at least once
        assert pe._model.predict.call_count >= 1

    async def test_motor_commands_published(self, bus: EventBus):
        """Motor commands should be published to the event bus."""
        pe = PolicyExecutor(bus=bus)
        pe._model = _make_mock_model()

        received = []
        async def capture(data):
            received.append(data)
        bus.subscribe(Events.MOTOR_COMMAND, capture)

        center = SIM_SIZE / 2
        await pe.navigate_waypoints([(center, center - 50)], timeout_per_wp=2.0)

        # Should have received at least one command + final stop
        assert len(received) >= 2
        # All should be MotorCommand instances
        for cmd in received:
            assert isinstance(cmd, MotorCommand)

    async def test_final_stop_published(self, bus: EventBus):
        """The last motor command should be a stop (0, 0)."""
        pe = PolicyExecutor(bus=bus)
        pe._model = _make_mock_model()

        received = []
        async def capture(data):
            received.append(data)
        bus.subscribe(Events.MOTOR_COMMAND, capture)

        center = SIM_SIZE / 2
        await pe.navigate_waypoints([(center, center - 50)], timeout_per_wp=2.0)

        assert len(received) >= 1
        last = received[-1]
        assert last.left == pytest.approx(0.0)
        assert last.right == pytest.approx(0.0)

    async def test_max_steps_safety(self, bus: EventBus):
        """If model keeps predicting 'stop', we should hit the step limit gracefully."""
        # "stop" skill: index 4/8 = 0.5
        def always_stop(obs, deterministic=True):
            return np.array([4.0 / 8, 0.5, 0.1], dtype=np.float32), None

        pe = PolicyExecutor(bus=bus)
        pe._model = _make_mock_model(always_stop)

        center = SIM_SIZE / 2
        # Far-away goal — stop skill won't reach it
        result = await pe.navigate_waypoints(
            [(center + 200, center)], timeout_per_wp=5.0,
        )
        # Should have terminated without error (via step limit or timeout)
        assert pe._model.predict.call_count <= MAX_STEPS_PER_WAYPOINT

    async def test_navigate_multiple_waypoints(self, bus: EventBus):
        """Should attempt each waypoint in sequence."""
        call_count = [0]

        def counting_forward(obs, deterministic=True):
            call_count[0] += 1
            return np.array([0.0, 0.5, 0.2], dtype=np.float32), None

        pe = PolicyExecutor(bus=bus)
        pe._model = _make_mock_model(counting_forward)

        center = SIM_SIZE / 2
        waypoints = [
            (center, center - 30),  # close ahead
            (center + 30, center - 30),  # close right-ahead
        ]
        await pe.navigate_waypoints(waypoints, timeout_per_wp=2.0)
        # Should have made predictions for both waypoints
        assert call_count[0] >= 2


class TestNavFormat:
    """Tests for nav-format models (8D obs, 4 skills)."""

    def test_nav_obs_shape(self, bus: EventBus):
        pe = PolicyExecutor(bus=bus)
        pe._nav_format = True
        obs = pe._get_obs((400.0, 100.0))
        assert obs.shape == (8,)
        assert obs.dtype == np.float32

    def test_nav_obs_includes_relative_bearing(self, bus: EventBus):
        """Nav obs should encode relative bearing to goal."""
        pe = PolicyExecutor(bus=bus)
        pe._nav_format = True
        # Robot at center facing up (-pi/2), goal directly ahead
        center = SIM_SIZE / 2
        obs = pe._get_obs((center, center - 100))
        # Relative bearing should be ~0 (goal is straight ahead)
        # obs[5] = sin(rel_bearing), obs[6] = cos(rel_bearing)
        assert obs[6] == pytest.approx(1.0, abs=0.1)  # cos(0) ≈ 1

    def test_nav_decode_forward(self, bus: EventBus):
        """action[0]=0 should map to 'forward' in nav format."""
        pe = PolicyExecutor(bus=bus)
        pe._nav_format = True
        action = np.array([0.0, 0.5, 0.5], dtype=np.float32)
        name, _, speed, dur = pe._decode_action(action)
        assert name == "forward"

    def test_nav_decode_right(self, bus: EventBus):
        """action[0] near 1.0 should map to 'right' in nav format."""
        pe = PolicyExecutor(bus=bus)
        pe._nav_format = True
        action = np.array([0.99, 0.5, 0.5], dtype=np.float32)
        name, _, speed, dur = pe._decode_action(action)
        assert name == "right"

    def test_legacy_obs_shape(self, bus: EventBus):
        """Legacy format should produce 6D obs."""
        pe = PolicyExecutor(bus=bus)
        pe._nav_format = False
        obs = pe._get_obs((400.0, 100.0))
        assert obs.shape == (6,)

    async def test_nav_navigate_forward(self, bus: EventBus):
        """Nav-format model predicting forward should move robot."""
        def nav_forward(obs, deterministic=True):
            return np.array([0.0, 0.8, 0.5], dtype=np.float32), None

        pe = PolicyExecutor(bus=bus)
        pe._model = _make_mock_model(nav_forward)
        pe._nav_format = True

        received = []
        async def capture(data):
            received.append(data)
        bus.subscribe(Events.MOTOR_COMMAND, capture)

        center = SIM_SIZE / 2
        await pe.navigate_waypoints([(center, center - 50)], timeout_per_wp=3.0)

        # Should have published motor commands
        assert len(received) >= 2
        # Final command is stop
        assert received[-1].left == pytest.approx(0.0)
        assert received[-1].right == pytest.approx(0.0)
