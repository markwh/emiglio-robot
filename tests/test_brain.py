"""Tests for the brain module — command parsing and BrainClient."""

from unittest.mock import patch

from emiglio.brain import BrainClient, parse_commands


def test_parse_commands_extracts_move():
    text = "Sure! [COMMAND:move:forward] I'll go forward!"
    clean, commands = parse_commands(text)
    assert len(commands) == 1
    assert commands[0] == {"action": "move", "params": "forward"}
    assert "[COMMAND" not in clean
    assert "I'll go forward!" in clean


def test_parse_commands_multiple():
    text = "[COMMAND:move:left] Let me turn. [COMMAND:speak:hello]"
    clean, commands = parse_commands(text)
    assert len(commands) == 2
    assert commands[0]["action"] == "move"
    assert commands[1]["action"] == "speak"


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
    import pytest
    with pytest.raises(ValueError, match="Unknown brain_mode"):
        BrainClient(mode="banana")
