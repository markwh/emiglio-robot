"""LangGraph agent builder for Emiglio's brain."""

from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

from prompts import SYSTEM_PROMPT
from tools import ALL_TOOLS, TOOL_TO_COMMAND


def build_agent(api_key: str, model: str = "claude-sonnet-4-5-20250929"):
    """Build and return a compiled LangGraph ReAct agent."""
    llm = ChatAnthropic(
        model=model,
        max_tokens=256,
        api_key=api_key,
    )
    return create_react_agent(llm, ALL_TOOLS, prompt=SYSTEM_PROMPT)


def extract_reply(messages: list) -> str:
    """Extract the final AI text response from agent output messages."""
    for msg in reversed(messages):
        if msg.type == "ai" and msg.content:
            # content can be a string or a list of content blocks
            if isinstance(msg.content, str):
                return msg.content
            # For list content, concatenate text blocks
            parts = []
            for block in msg.content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block["text"])
            if parts:
                return " ".join(parts)
    return ""


def extract_commands(messages: list) -> list[dict]:
    """Walk messages for tool calls and translate them to command dicts.

    Returns list of {"action": "move", "params": "forward"} etc.
    """
    commands = []
    for msg in messages:
        if msg.type == "ai" and hasattr(msg, "tool_calls"):
            for tc in msg.tool_calls:
                name = tc["name"]
                if name in TOOL_TO_COMMAND:
                    cmd = TOOL_TO_COMMAND[name].copy()
                    args = tc.get("args", {})
                    if "speed" in args:
                        cmd["speed"] = args["speed"]
                    if "duration" in args:
                        cmd["duration"] = args["duration"]
                    commands.append(cmd)
    return commands
