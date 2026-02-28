"""Tests for the brain service command parsing.

The parse_commands function is duplicated here since server/brain/app.py
has heavy dependencies (anthropic) that aren't part of the Pi-side package.
"""

import re


def parse_commands(text: str) -> tuple[str, list[dict]]:
    """Extract [COMMAND:action:params] from response text."""
    commands = []
    clean_text = text
    for match in re.finditer(r'\[COMMAND:(\w+):([^\]]+)\]', text):
        action = match.group(1)
        params = match.group(2)
        commands.append({"action": action, "params": params})
        clean_text = clean_text.replace(match.group(0), "")
    return clean_text.strip(), commands


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
