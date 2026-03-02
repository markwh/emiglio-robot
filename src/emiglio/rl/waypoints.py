"""Waypoint generators for RL-driven compound navigation skills.

Each function returns a list of (x, y) waypoints in sim coordinates.
The robot starts at center (250, 250) facing up (heading = -pi/2).
"""

from __future__ import annotations

import math
from typing import Callable

from emiglio.rl.sim import SIM_SIZE, MARGIN

_CENTER = SIM_SIZE / 2


def patrol_waypoints(
    speed_factor: float = 1.0, duration: float = 4.0,
) -> list[tuple[float, float]]:
    """4 corners of a rectangle ahead of the starting position (CW loop)."""
    side = min(80 * (duration / 4.0), 180)
    half = side / 2
    # Forward is -y in sim coordinates; build rectangle ahead of center
    # Waypoints: front-left → front-right → back-right → back-left
    return [
        (_CENTER - half, _CENTER - side),   # front-left
        (_CENTER + half, _CENTER - side),   # front-right
        (_CENTER + half, _CENTER),          # back-right (return row)
        (_CENTER - half, _CENTER),          # back-left  (close loop)
    ]


def circle_waypoints(
    speed_factor: float = 1.0, duration: float = 4.5,
) -> list[tuple[float, float]]:
    """8 evenly-spaced points on a circle, centered ahead of the robot."""
    radius = min(60 * (duration / 4.5), 150)
    # Circle center is directly ahead (above) the start position
    cx, cy = _CENTER, _CENTER - radius
    n_points = 8
    pts: list[tuple[float, float]] = []
    for i in range(n_points):
        angle = 2 * math.pi * i / n_points - math.pi / 2  # start at bottom of circle (robot's position)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        # Clamp to arena
        x = max(MARGIN, min(SIM_SIZE - MARGIN, x))
        y = max(MARGIN, min(SIM_SIZE - MARGIN, y))
        pts.append((x, y))
    return pts


def zigzag_waypoints(
    speed_factor: float = 1.0, duration: float = 3.0,
) -> list[tuple[float, float]]:
    """4 points alternating left-right while advancing forward."""
    depth = min(50 * (duration / 3.0), 140)  # total forward distance
    width = min(40 * (duration / 3.0), 100)  # lateral offset
    step_y = depth / 4  # forward step per waypoint
    pts: list[tuple[float, float]] = []
    for i in range(4):
        x_offset = width if (i % 2 == 0) else -width
        y_offset = -step_y * (i + 1)  # forward is -y
        pts.append((_CENTER + x_offset, _CENTER + y_offset))
    return pts


def rush_waypoints(
    speed_factor: float = 1.0, duration: float = 3.0,
) -> list[tuple[float, float]]:
    """Single waypoint far ahead of the starting position."""
    dist = min(120 * (duration / 3.0), 220)
    y = max(MARGIN, _CENTER - dist)  # forward is -y
    return [(_CENTER, y)]


def pentagram_waypoints(
    speed_factor: float = 1.0, duration: float = 5.0,
) -> list[tuple[float, float]]:
    """5 points of a pentagram (star shape), drawn in star-stroke order.

    A pentagram visits vertices 0→2→4→1→3→0 (skipping one each time)
    to trace the five-pointed star without lifting.
    """
    radius = min(80 * (duration / 5.0), 180)
    # Center the star slightly ahead of robot start
    cx, cy = _CENTER, _CENTER - radius * 0.3

    # 5 vertices evenly spaced, starting at top (-pi/2)
    vertices: list[tuple[float, float]] = []
    for i in range(5):
        angle = -math.pi / 2 + 2 * math.pi * i / 5
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        x = max(MARGIN, min(SIM_SIZE - MARGIN, x))
        y = max(MARGIN, min(SIM_SIZE - MARGIN, y))
        vertices.append((x, y))

    # Star-stroke order: 0 → 2 → 4 → 1 → 3 (→ back to 0 closes the star)
    star_order = [0, 2, 4, 1, 3]
    return [vertices[i] for i in star_order]


WAYPOINT_GENERATORS: dict[str, Callable[..., list[tuple[float, float]]]] = {
    "patrol": patrol_waypoints,
    "circle": circle_waypoints,
    "zigzag": zigzag_waypoints,
    "rush": rush_waypoints,
    "pentagram": pentagram_waypoints,
}
