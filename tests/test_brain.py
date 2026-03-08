"""Tests for the brain LangGraph agent integration.

Tests the tool-to-command mapping, message extraction logic, and
BrainClient without making any API calls.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from emiglio.brain import BrainClient, extract_commands, extract_reply
from emiglio.brain.tools import ALL_TOOLS, TOOL_TO_COMMAND


# --- TOOL_TO_COMMAND mapping tests ---


def test_tool_to_command_covers_all_tools():
    """Every tool in ALL_TOOLS must have a mapping in TOOL_TO_COMMAND."""
    tool_names = {t.name for t in ALL_TOOLS}
    mapped_names = set(TOOL_TO_COMMAND.keys())
    assert tool_names == mapped_names


def test_tool_to_command_all_are_move_actions():
    """All commands should have action='move'."""
    for name, cmd in TOOL_TO_COMMAND.items():
        assert cmd["action"] == "move", f"{name} has action={cmd['action']}"


def test_tool_to_command_params_match_conversation_presets():
    """Params must be one of the directions/compound moves conversation.py expects."""
    valid_params = {
        "forward", "backward", "left", "right", "stop",
        "spin", "wiggle", "dance", "patrol", "circle", "zigzag", "rush",
    }
    for name, cmd in TOOL_TO_COMMAND.items():
        assert cmd["params"] in valid_params, f"{name} has params={cmd['params']}"


def test_tool_to_command_returns_copies():
    """extract_commands should return copies, not references to the shared dict."""
    msg = _make_ai_message_with_tool_calls([{"name": "move_forward", "args": {}, "id": "1"}])
    commands = extract_commands([msg])
    # Mutating the returned dict should not affect TOOL_TO_COMMAND
    commands[0]["extra"] = True
    assert "extra" not in TOOL_TO_COMMAND["move_forward"]


# --- extract_reply tests ---


def test_extract_reply_simple_string():
    msg = _make_ai_message("Hello there!")
    assert extract_reply([msg]) == "Hello there!"


def test_extract_reply_takes_last_ai_message():
    msg1 = _make_ai_message("First response")
    msg2 = _make_ai_message("Final response")
    assert extract_reply([msg1, msg2]) == "Final response"


def test_extract_reply_skips_non_ai_messages():
    human = MagicMock()
    human.type = "human"
    human.content = "User input"
    ai = _make_ai_message("Robot reply")
    assert extract_reply([human, ai]) == "Robot reply"


def test_extract_reply_handles_list_content():
    msg = MagicMock()
    msg.type = "ai"
    msg.content = [{"type": "text", "text": "Part one"}, {"type": "text", "text": "Part two"}]
    assert extract_reply([msg]) == "Part one Part two"


def test_extract_reply_empty_messages():
    assert extract_reply([]) == ""


def test_extract_reply_skips_ai_with_empty_content():
    """AI messages with empty content (e.g. tool-call-only turns) should be skipped."""
    empty_ai = MagicMock()
    empty_ai.type = "ai"
    empty_ai.content = ""
    real_ai = _make_ai_message("The real reply")
    assert extract_reply([real_ai, empty_ai]) == "The real reply"


# --- extract_commands tests ---


def test_extract_commands_single_tool_call():
    msg = _make_ai_message_with_tool_calls([
        {"name": "move_forward", "args": {}, "id": "tc1"},
    ])
    commands = extract_commands([msg])
    assert commands == [{"action": "move", "params": "forward"}]


def test_extract_commands_multiple_tool_calls():
    msg = _make_ai_message_with_tool_calls([
        {"name": "turn_left", "args": {}, "id": "tc1"},
        {"name": "move_forward", "args": {}, "id": "tc2"},
    ])
    commands = extract_commands([msg])
    assert len(commands) == 2
    assert commands[0] == {"action": "move", "params": "left"}
    assert commands[1] == {"action": "move", "params": "forward"}


def test_extract_commands_across_multiple_messages():
    msg1 = _make_ai_message_with_tool_calls([
        {"name": "move_forward", "args": {}, "id": "tc1"},
    ])
    msg2 = _make_ai_message_with_tool_calls([
        {"name": "stop", "args": {}, "id": "tc2"},
    ])
    commands = extract_commands([msg1, msg2])
    assert len(commands) == 2
    assert commands[0]["params"] == "forward"
    assert commands[1]["params"] == "stop"


def test_extract_commands_ignores_unknown_tools():
    msg = _make_ai_message_with_tool_calls([
        {"name": "unknown_tool", "args": {}, "id": "tc1"},
        {"name": "turn_right", "args": {}, "id": "tc2"},
    ])
    commands = extract_commands([msg])
    assert len(commands) == 1
    assert commands[0] == {"action": "move", "params": "right"}


def test_extract_commands_no_tool_calls():
    msg = _make_ai_message("Just text, no tools")
    commands = extract_commands([msg])
    assert commands == []


def test_extract_commands_skips_human_messages():
    human = MagicMock()
    human.type = "human"
    ai = _make_ai_message_with_tool_calls([
        {"name": "move_backward", "args": {}, "id": "tc1"},
    ])
    commands = extract_commands([human, ai])
    assert len(commands) == 1
    assert commands[0]["params"] == "backward"


# --- BrainClient tests ---


def test_brain_client_available():
    """BrainClient.available reflects whether the agent was created."""
    brain = BrainClient(model="claude-sonnet-4-5-20250929")
    # May or may not be available depending on ANTHROPIC_API_KEY
    assert isinstance(brain.available, bool)


async def test_brain_client_no_agent_returns_fallback():
    """BrainClient with no agent returns a fallback reply."""
    brain = BrainClient()
    brain._agent = None
    result = await brain.think("hello")
    assert "brain isn't connected" in result["reply"]
    assert result["commands"] == []


# --- extract_commands with tool args tests ---


def test_extract_commands_with_speed_arg():
    """Tool call with speed arg should merge into command dict."""
    msg = _make_ai_message_with_tool_calls([
        {"name": "move_forward", "args": {"speed": 0.5, "duration": 2.0}, "id": "tc1"},
    ])
    commands = extract_commands([msg])
    assert len(commands) == 1
    assert commands[0]["params"] == "forward"
    assert commands[0]["speed"] == pytest.approx(0.5)
    assert commands[0]["duration"] == pytest.approx(2.0)


def test_extract_commands_without_args():
    """Tool call with no args should not add speed/duration keys."""
    msg = _make_ai_message_with_tool_calls([
        {"name": "move_forward", "args": {}, "id": "tc1"},
    ])
    commands = extract_commands([msg])
    assert len(commands) == 1
    assert "speed" not in commands[0]
    assert "duration" not in commands[0]


def test_extract_commands_compound_tool():
    """Compound tool like spin should be mapped correctly."""
    msg = _make_ai_message_with_tool_calls([
        {"name": "spin", "args": {"speed": 0.7}, "id": "tc1"},
    ])
    commands = extract_commands([msg])
    assert len(commands) == 1
    assert commands[0] == {"action": "move", "params": "spin", "speed": 0.7}


# --- Helpers ---


def _make_ai_message(text: str) -> MagicMock:
    """Create a mock AI message with string content and no tool calls."""
    msg = MagicMock()
    msg.type = "ai"
    msg.content = text
    msg.tool_calls = []
    return msg


def _make_ai_message_with_tool_calls(tool_calls: list[dict]) -> MagicMock:
    """Create a mock AI message with tool calls."""
    msg = MagicMock()
    msg.type = "ai"
    msg.content = ""
    msg.tool_calls = tool_calls
    return msg
