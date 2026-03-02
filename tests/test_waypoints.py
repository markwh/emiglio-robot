"""Tests for RL waypoint generators."""

from emiglio.rl.sim import SIM_SIZE, MARGIN
from emiglio.rl.waypoints import (
    WAYPOINT_GENERATORS,
    patrol_waypoints,
    circle_waypoints,
    zigzag_waypoints,
    rush_waypoints,
    pentagram_waypoints,
)


class TestWaypointCounts:
    def test_patrol_4_waypoints(self):
        pts = patrol_waypoints()
        assert len(pts) == 4

    def test_circle_8_waypoints(self):
        pts = circle_waypoints()
        assert len(pts) == 8

    def test_zigzag_4_waypoints(self):
        pts = zigzag_waypoints()
        assert len(pts) == 4

    def test_rush_1_waypoint(self):
        pts = rush_waypoints()
        assert len(pts) == 1

    def test_pentagram_5_waypoints(self):
        pts = pentagram_waypoints()
        assert len(pts) == 5


class TestWaypointBounds:
    def test_all_within_arena(self):
        """All generated waypoints should stay within the arena bounds."""
        for name, gen in WAYPOINT_GENERATORS.items():
            pts = gen()
            for i, (x, y) in enumerate(pts):
                assert MARGIN <= x <= SIM_SIZE - MARGIN, (
                    f"{name} waypoint {i}: x={x} out of bounds"
                )
                assert MARGIN <= y <= SIM_SIZE - MARGIN, (
                    f"{name} waypoint {i}: y={y} out of bounds"
                )

    def test_all_within_arena_long_duration(self):
        """Even with max duration, waypoints should be in-bounds."""
        for name, gen in WAYPOINT_GENERATORS.items():
            pts = gen(duration=5.0)
            for i, (x, y) in enumerate(pts):
                assert MARGIN <= x <= SIM_SIZE - MARGIN, (
                    f"{name} waypoint {i} (dur=5): x={x} out of bounds"
                )
                assert MARGIN <= y <= SIM_SIZE - MARGIN, (
                    f"{name} waypoint {i} (dur=5): y={y} out of bounds"
                )


class TestWaypointRegistry:
    def test_generators_registry(self):
        """All 4 nav skills should be in the registry."""
        assert set(WAYPOINT_GENERATORS.keys()) == {"patrol", "circle", "zigzag", "rush", "pentagram"}

    def test_generators_callable(self):
        """All generators should be callable with no args."""
        for name, gen in WAYPOINT_GENERATORS.items():
            pts = gen()
            assert isinstance(pts, list)
            assert all(isinstance(p, tuple) and len(p) == 2 for p in pts)
