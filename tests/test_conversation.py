"""Tests for the conversation manager."""

import base64

import pytest
from unittest.mock import AsyncMock, MagicMock

from emiglio.event_bus import EventBus
from emiglio.models import Events, MotorCommand
from emiglio.conversation import ConversationManager, MOVE_PRESETS


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
