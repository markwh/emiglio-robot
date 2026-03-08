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
def dance(speed: float = 1.0, duration: float = 2.0) -> str:
    """Make the robot do a little dance. Celebratory! Speed 0.1-1.0, duration 0.1-5.0 seconds (default 2.0)."""
    return f"Dancing (speed={speed}, duration={duration})."


@tool
def patrol(speed: float = 1.0, duration: float = 4.0) -> str:
    """Drive a rectangular patrol loop — 4 forward legs with 90-degree turns. Good for surveying an area. Speed 0.1-1.0, duration 0.1-5.0 seconds (default 4.0)."""
    return f"Patrolling (speed={speed}, duration={duration})."


@tool
def circle(speed: float = 1.0, duration: float = 4.5) -> str:
    """Drive in a circle. Speed 0.1-1.0, duration 0.1-5.0 seconds (default 4.5)."""
    return f"Circling (speed={speed}, duration={duration})."


@tool
def zigzag(speed: float = 1.0, duration: float = 3.0) -> str:
    """Zigzag forward with alternating lateral sweeps. Covers ground with a wide path. Speed 0.1-1.0, duration 0.1-5.0 seconds (default 3.0)."""
    return f"Zigzagging (speed={speed}, duration={duration})."


@tool
def rush(speed: float = 1.0, duration: float = 3.0) -> str:
    """Rush forward at full power in a straight line. Covers maximum ground quickly. Speed 0.1-1.0, duration 0.1-5.0 seconds (default 3.0)."""
    return f"Rushing (speed={speed}, duration={duration})."


ALL_TOOLS = [
    move_forward, move_backward, turn_left, turn_right, stop,
    spin, wiggle, dance, patrol, circle, zigzag, rush,
]

# Maps tool names to the command format that conversation.py expects
TOOL_TO_COMMAND: dict[str, dict[str, str]] = {
    "move_forward": {"action": "move", "params": "forward"},
    "move_backward": {"action": "move", "params": "backward"},
    "turn_left": {"action": "move", "params": "left"},
    "turn_right": {"action": "move", "params": "right"},
    "stop": {"action": "move", "params": "stop"},
    "spin": {"action": "move", "params": "spin"},
    "wiggle": {"action": "move", "params": "wiggle"},
    "dance": {"action": "move", "params": "dance"},
    "patrol": {"action": "move", "params": "patrol"},
    "circle": {"action": "move", "params": "circle"},
    "zigzag": {"action": "move", "params": "zigzag"},
    "rush": {"action": "move", "params": "rush"},
}
