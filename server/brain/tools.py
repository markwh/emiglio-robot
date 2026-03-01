"""LangChain tool definitions for Emiglio's movement commands."""

from langchain_core.tools import tool


@tool
def move_forward(speed: float = 1.0, duration: float = 1.0) -> str:
    """Move the robot forward. Speed 0.1-1.0 (default 1.0), duration 0.1-5.0 seconds (default 1.0)."""
    return f"Moving forward (speed={speed}, duration={duration})."


@tool
def move_backward(speed: float = 1.0, duration: float = 1.0) -> str:
    """Move the robot backward. Speed 0.1-1.0 (default 1.0), duration 0.1-5.0 seconds (default 1.0)."""
    return f"Moving backward (speed={speed}, duration={duration})."


@tool
def turn_left(speed: float = 1.0, duration: float = 1.0) -> str:
    """Turn the robot to the left. Speed 0.1-1.0 (default 1.0), duration 0.1-5.0 seconds (default 1.0)."""
    return f"Turning left (speed={speed}, duration={duration})."


@tool
def turn_right(speed: float = 1.0, duration: float = 1.0) -> str:
    """Turn the robot to the right. Speed 0.1-1.0 (default 1.0), duration 0.1-5.0 seconds (default 1.0)."""
    return f"Turning right (speed={speed}, duration={duration})."


@tool
def stop() -> str:
    """Stop the robot's movement."""
    return "Stopped."


@tool
def spin(speed: float = 1.0, duration: float = 1.0) -> str:
    """Spin the robot in place. Fun and expressive! Speed 0.1-1.0, duration 0.1-5.0 seconds."""
    return f"Spinning (speed={speed}, duration={duration})."


@tool
def wiggle(speed: float = 1.0, duration: float = 1.0) -> str:
    """Wiggle the robot back and forth. Playful! Speed 0.1-1.0, duration 0.1-5.0 seconds."""
    return f"Wiggling (speed={speed}, duration={duration})."


@tool
def dance(speed: float = 1.0, duration: float = 1.0) -> str:
    """Make the robot do a little dance. Celebratory! Speed 0.1-1.0, duration 0.1-5.0 seconds."""
    return f"Dancing (speed={speed}, duration={duration})."


ALL_TOOLS = [move_forward, move_backward, turn_left, turn_right, stop, spin, wiggle, dance]

# Maps tool names to the command format that conversation.py expects:
# {"action": "move", "params": "forward|backward|left|right|stop|spin|wiggle|dance"}
TOOL_TO_COMMAND: dict[str, dict[str, str]] = {
    "move_forward": {"action": "move", "params": "forward"},
    "move_backward": {"action": "move", "params": "backward"},
    "turn_left": {"action": "move", "params": "left"},
    "turn_right": {"action": "move", "params": "right"},
    "stop": {"action": "move", "params": "stop"},
    "spin": {"action": "move", "params": "spin"},
    "wiggle": {"action": "move", "params": "wiggle"},
    "dance": {"action": "move", "params": "dance"},
}
