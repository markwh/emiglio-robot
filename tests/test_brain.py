"""Tests for the brain service LangGraph integration and Pi-side BrainClient.

Tests the tool-to-command mapping, message extraction logic, and
inline brain client without making any API calls.
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add the brain service directory to the path so we can import its modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "server" / "brain"))

from tools import ALL_TOOLS, TOOL_TO_COMMAND
from graph import extract_commands, extract_reply
from emiglio.brain import BrainClient, parse_commands


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
    """Params must be one of the directions conversation.py expects."""
    valid_params = {"forward", "backward", "left", "right", "stop"}
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


# --- Pi-side BrainClient tests ---


def test_parse_commands_none():
    text = "Just a regular response with no commands."
    clean, commands = parse_commands(text)
    assert len(commands) == 0
    assert clean == text


def test_brain_client_inline_mode():
    """BrainClient in inline mode creates an Anthropic client (or warns if no key)."""
    brain = BrainClient(mode="inline", model="claude-sonnet-4-5-20250929")
    assert brain._mode == "inline"
    # Client may or may not be available depending on ANTHROPIC_API_KEY
    assert isinstance(brain.available, bool)


def test_brain_client_server_mode():
    """BrainClient in server mode creates an HTTP client."""
    brain = BrainClient(mode="server")
    assert brain._mode == "server"
    assert brain.available is True
    assert brain._http is not None


def test_brain_client_invalid_mode():
    """BrainClient raises ValueError for unknown mode."""
    with pytest.raises(ValueError, match="Unknown brain_mode"):
        BrainClient(mode="banana")


# --- Multimodal vision tests ---


async def test_think_inline_with_image():
    """_think_inline should send multimodal content blocks when image_base64 is provided."""
    brain = BrainClient(mode="inline")
    if brain._anthropic is None:
        pytest.skip("No Anthropic client available")

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="I can see something.")]

    brain._anthropic.messages.create = AsyncMock(return_value=mock_response)
    result = await brain._think_inline("what do you see?", "", "base64data")
    assert result["reply"] == "I can see something."

    call_kwargs = brain._anthropic.messages.create.call_args.kwargs
    content = call_kwargs["messages"][0]["content"]
    assert isinstance(content, list)
    assert content[0]["type"] == "image"
    assert content[0]["source"]["data"] == "base64data"
    assert content[1]["type"] == "text"


async def test_think_inline_without_image():
    """_think_inline without image should send text-only content blocks."""
    brain = BrainClient(mode="inline")
    if brain._anthropic is None:
        pytest.skip("No Anthropic client available")

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Hello.")]

    brain._anthropic.messages.create = AsyncMock(return_value=mock_response)
    result = await brain._think_inline("hello", "")
    assert result["reply"] == "Hello."

    call_kwargs = brain._anthropic.messages.create.call_args.kwargs
    content = call_kwargs["messages"][0]["content"]
    assert isinstance(content, list)
    assert len(content) == 1
    assert content[0]["type"] == "text"


async def test_think_server_includes_image():
    """_think_server should include image_base64 in the POST payload."""
    brain = BrainClient(mode="server")

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"reply": "I see it!", "commands": []}
    mock_resp.raise_for_status = MagicMock()

    brain._http.post = AsyncMock(return_value=mock_resp)
    result = await brain._think_server("what is this?", "", "http://localhost:8003", "imagedata123")
    assert result["reply"] == "I see it!"

    call_kwargs = brain._http.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs[1]["json"]
    assert payload["image_base64"] == "imagedata123"
    assert payload["transcript"] == "what is this?"


async def test_think_server_no_image():
    """_think_server without image should not include image_base64 in payload."""
    brain = BrainClient(mode="server")

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"reply": "Hi!", "commands": []}
    mock_resp.raise_for_status = MagicMock()

    brain._http.post = AsyncMock(return_value=mock_resp)
    await brain._think_server("hello", "", "http://localhost:8003")

    call_kwargs = brain._http.post.call_args
    payload = call_kwargs.kwargs.get("json") or call_kwargs[1]["json"]
    assert "image_base64" not in payload


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
