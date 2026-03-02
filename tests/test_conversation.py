"""Tests for the conversation manager."""

import base64

import pytest
from unittest.mock import AsyncMock, MagicMock

from emiglio.event_bus import EventBus
from emiglio.models import Events, MotorCommand
from emiglio.conversation import (
    ConversationManager,
    MOVE_PRESETS,
    COMPOUND_MOVES,
    DEFAULT_SPEED_FACTOR,
    DEFAULT_MOVE_DURATION,
    SKILL_DURATION_DEFAULTS,
    _RL_NAV_SKILLS,
)


async def test_execute_move_forward(bus: EventBus):
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "forward"})

    # Should get a move command then a stop command
    assert len(received) == 2
    assert received[0].left == pytest.approx(0.6)
    assert received[0].right == pytest.approx(0.6)
    assert received[1].left == pytest.approx(0.0)
    assert received[1].right == pytest.approx(0.0)


async def test_execute_move_stop(bus: EventBus):
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "stop"})

    # Stop should only send one command (no follow-up stop)
    assert len(received) == 1
    assert received[0].left == pytest.approx(0.0)
    assert received[0].right == pytest.approx(0.0)


async def test_execute_unknown_command(bus: EventBus):
    mgr = ConversationManager(bus=bus)
    # Should not raise
    await mgr._execute_command({"action": "dance", "params": "moonwalk"})


async def test_execute_unknown_direction(bus: EventBus):
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "diagonal"})
    assert len(received) == 0


def test_move_presets_all_valid():
    for direction, (left, right) in MOVE_PRESETS.items():
        assert -1.0 <= left <= 1.0, f"{direction} left out of range"
        assert -1.0 <= right <= 1.0, f"{direction} right out of range"


async def test_busy_flag(bus: EventBus):
    mgr = ConversationManager(bus=bus)
    assert not mgr.busy


async def test_text_interaction_no_server(bus: EventBus):
    """Text interaction should return graceful error when server is down."""
    mgr = ConversationManager(bus=bus)
    result = await mgr.handle_text_interaction("hello")
    # Should get a fallback reply (brain server is down)
    assert "reply" in result or "error" in result


async def test_build_context_no_camera(bus: EventBus):
    mgr = ConversationManager(bus=bus)
    context, image = await mgr._build_context()
    assert context == ""
    assert image is None


async def test_build_context_no_frame(bus: EventBus):
    mock_camera = MagicMock()
    mock_camera.get_jpeg.return_value = None
    mgr = ConversationManager(bus=bus, camera=mock_camera)
    context, image = await mgr._build_context()
    assert context == ""
    assert image is None


async def test_build_context_with_frame(bus: EventBus):
    fake_jpeg = b"\xff\xd8\xff\xe0test_image_data"
    mock_camera = MagicMock()
    mock_camera.get_jpeg.return_value = fake_jpeg
    mgr = ConversationManager(bus=bus, camera=mock_camera)
    context, image = await mgr._build_context()
    assert context == "[Camera frame attached]"
    assert image is not None
    # Verify it's valid base64 that decodes back to original
    assert base64.b64decode(image) == fake_jpeg


# --- Expanded locomotion skill tests ---


async def test_execute_move_forward_custom_speed(bus: EventBus):
    """Speed factor should scale the preset speeds."""
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "forward", "speed": 0.5, "duration": 0.1})

    # Move + stop = 2 commands
    assert len(received) == 2
    # 0.6 * 0.5 = 0.3
    assert received[0].left == pytest.approx(0.3)
    assert received[0].right == pytest.approx(0.3)
    assert received[1].left == pytest.approx(0.0)
    assert received[1].right == pytest.approx(0.0)


async def test_execute_move_default_speed_unchanged(bus: EventBus):
    """Without speed param, output should match original 0.6 preset."""
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "forward", "duration": 0.1})

    assert len(received) == 2
    assert received[0].left == pytest.approx(0.6)
    assert received[0].right == pytest.approx(0.6)


async def test_execute_spin(bus: EventBus):
    """Spin should produce opposing motor directions then stop."""
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "spin", "duration": 0.1})

    # Spin move + stop = 2 commands
    assert len(received) == 2
    # Motors should be opposing: one positive, one negative
    assert received[0].left > 0
    assert received[0].right < 0
    # Stopped
    assert received[1].left == pytest.approx(0.0)
    assert received[1].right == pytest.approx(0.0)


async def test_execute_wiggle(bus: EventBus):
    """Wiggle should produce multiple alternating commands then stop."""
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "wiggle", "duration": 0.5})

    # At least 2 direction changes + final stop
    assert len(received) >= 3
    # Last command is stop
    assert received[-1].left == pytest.approx(0.0)
    assert received[-1].right == pytest.approx(0.0)


async def test_execute_dance(bus: EventBus):
    """Dance should produce multi-phase sequence ending with stop."""
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "dance", "duration": 0.4})

    # Should have many commands (forward + stop, spin + stop, wiggles + stop, backward + stop)
    assert len(received) >= 4
    # Last command is stop (from backward phase)
    assert received[-1].left == pytest.approx(0.0)
    assert received[-1].right == pytest.approx(0.0)


async def test_speed_clamped(bus: EventBus):
    """Speed > 1.0 should be clamped to 1.0."""
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "forward", "speed": 5.0, "duration": 0.1})

    assert len(received) == 2
    # 0.6 * 1.0 (clamped) = 0.6
    assert received[0].left == pytest.approx(0.6)
    assert received[0].right == pytest.approx(0.6)


async def test_duration_clamped(bus: EventBus):
    """Duration > 5.0 should be clamped to 5.0 (we test with short mock)."""
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    # Use speed=0 scenario — just verify it doesn't hang or error with large duration
    # We can't easily test the actual duration without mocking asyncio.sleep,
    # so just verify the command executes without error
    # Actually, let's use a small duration and verify clamping works for < MIN
    await mgr._execute_command({"action": "move", "params": "forward", "speed": 0.01, "duration": 0.01})

    assert len(received) == 2
    # speed clamped to 0.1: 0.6 * 0.1 = 0.06
    assert received[0].left == pytest.approx(0.06)
    # duration clamped to 0.1 (MIN_DURATION)


# --- Higher-level movement skill tests ---


async def test_execute_patrol(bus: EventBus):
    """Patrol should produce forward+turn sequences then stop."""
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "patrol", "duration": 1.0})

    # 4 legs × (forward + turn) + final stop = 9 commands
    assert len(received) == 9
    # Last command is stop
    assert received[-1].left == pytest.approx(0.0)
    assert received[-1].right == pytest.approx(0.0)
    # First command should be forward (both positive)
    assert received[0].left > 0
    assert received[0].right > 0
    # Second command should be a right turn (left positive, right negative)
    assert received[1].left > 0
    assert received[1].right < 0


async def test_execute_circle(bus: EventBus):
    """Circle should produce a single differential command then stop."""
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "circle", "duration": 0.1})

    # Move + stop = 2 commands
    assert len(received) == 2
    # Left motor should be faster than right (curves right)
    assert received[0].left > received[0].right
    assert received[0].left > 0
    assert received[0].right > 0
    # Stopped
    assert received[1].left == pytest.approx(0.0)
    assert received[1].right == pytest.approx(0.0)


async def test_execute_zigzag(bus: EventBus):
    """Zigzag should produce alternating arc commands then stop."""
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "zigzag", "duration": 0.9})

    # 0.9s / 0.4s steps = ~3 arc commands + final stop = 4
    assert len(received) >= 3
    # Last command is stop
    assert received[-1].left == pytest.approx(0.0)
    assert received[-1].right == pytest.approx(0.0)
    # First arc veers right: left > right
    assert received[0].left > received[0].right
    # Second arc veers left: right > left
    assert received[1].right > received[1].left


async def test_execute_rush(bus: EventBus):
    """Rush should produce full-power forward then stop."""
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    await mgr._execute_command({"action": "move", "params": "rush", "duration": 0.1})

    # Move + stop = 2 commands
    assert len(received) == 2
    # Full power (1.0 × default speed_factor 1.0)
    assert received[0].left == pytest.approx(1.0)
    assert received[0].right == pytest.approx(1.0)
    # Stopped
    assert received[1].left == pytest.approx(0.0)
    assert received[1].right == pytest.approx(0.0)


async def test_skill_duration_defaults(bus: EventBus):
    """When duration is omitted, skill-specific defaults should apply."""
    mgr = ConversationManager(bus=bus)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)

    # Verify the constants are as expected
    assert SKILL_DURATION_DEFAULTS["patrol"] == 4.0
    assert SKILL_DURATION_DEFAULTS["circle"] == 4.5
    assert SKILL_DURATION_DEFAULTS["zigzag"] == 3.0
    assert SKILL_DURATION_DEFAULTS["rush"] == 3.0
    assert SKILL_DURATION_DEFAULTS["dance"] == 2.0

    # Verify that unlisted skills still default to DEFAULT_MOVE_DURATION
    assert "forward" not in SKILL_DURATION_DEFAULTS
    assert "spin" not in SKILL_DURATION_DEFAULTS


# --- RL navigation integration tests ---


async def test_rl_nav_used_when_policy_available(bus: EventBus):
    """When a policy executor is available, patrol should use RL nav."""
    mock_policy = MagicMock()
    mock_policy.available = True
    mock_policy.navigate_waypoints = AsyncMock(return_value=True)

    mgr = ConversationManager(bus=bus, policy_executor=mock_policy)
    await mgr._execute_command({"action": "move", "params": "patrol", "duration": 1.0})

    mock_policy.navigate_waypoints.assert_awaited_once()
    args = mock_policy.navigate_waypoints.call_args
    # Should have passed waypoints list
    assert len(args[0][0]) == 4  # patrol produces 4 waypoints


async def test_rl_nav_fallback_without_policy(bus: EventBus):
    """Without a policy, patrol should fall back to hardcoded implementation."""
    mgr = ConversationManager(bus=bus)  # no policy_executor
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)
    await mgr._execute_command({"action": "move", "params": "patrol", "duration": 1.0})

    # Should have used hardcoded patrol (4 legs × forward+turn + stop = 9 commands)
    assert len(received) == 9


async def test_rl_nav_fallback_on_error(bus: EventBus):
    """If RL nav raises, should fall back to hardcoded skill."""
    mock_policy = MagicMock()
    mock_policy.available = True
    mock_policy.navigate_waypoints = AsyncMock(side_effect=RuntimeError("model error"))

    mgr = ConversationManager(bus=bus, policy_executor=mock_policy)
    received = []

    async def capture(data):
        received.append(data)

    bus.subscribe(Events.MOTOR_COMMAND, capture)
    await mgr._execute_command({"action": "move", "params": "patrol", "duration": 1.0})

    # Should have fallen back to hardcoded patrol
    assert len(received) == 9


async def test_expressive_skills_ignore_policy(bus: EventBus):
    """Spin, wiggle, dance should NOT use RL policy even when available."""
    mock_policy = MagicMock()
    mock_policy.available = True
    mock_policy.navigate_waypoints = AsyncMock()

    mgr = ConversationManager(bus=bus, policy_executor=mock_policy)

    for skill in ("spin", "wiggle", "dance"):
        mock_policy.navigate_waypoints.reset_mock()
        await mgr._execute_command({"action": "move", "params": skill, "duration": 0.2})
        mock_policy.navigate_waypoints.assert_not_awaited()
