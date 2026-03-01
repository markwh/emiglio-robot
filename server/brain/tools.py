"""LangChain tool definitions for Emiglio's movement commands."""

from langchain_core.tools import tool


@tool
def move_forward() -> str:
    """Move the robot forward briefly."""
    return "Moving forward."


@tool
def move_backward() -> str:
    """Move the robot backward briefly."""
    return "Moving backward."


@tool
def turn_left() -> str:
    """Turn the robot to the left."""
    return "Turning left."


@tool
def turn_right() -> str:
    """Turn the robot to the right."""
    return "Turning right."


@tool
def stop() -> str:
    """Stop the robot's movement."""
    return "Stopped."


ALL_TOOLS = [move_forward, move_backward, turn_left, turn_right, stop]

# Maps tool names to the command format that conversation.py expects:
# {"action": "move", "params": "forward|backward|left|right|stop"}
TOOL_TO_COMMAND: dict[str, dict[str, str]] = {
    "move_forward": {"action": "move", "params": "forward"},
    "move_backward": {"action": "move", "params": "backward"},
    "turn_left": {"action": "move", "params": "left"},
    "turn_right": {"action": "move", "params": "right"},
    "stop": {"action": "move", "params": "stop"},
}
