"""Synchronous skill executor that drives the Simulator.

Motor values mirror conversation.py so RL-trained behaviours transfer to the
real robot.
"""

from __future__ import annotations

from emiglio.rl.sim import Simulator

# Same presets as conversation.py
MOVE_PRESETS: dict[str, tuple[float, float]] = {
    "forward": (0.6, 0.6),
    "backward": (-0.6, -0.6),
    "left": (-0.5, 0.5),
    "right": (0.5, -0.5),
    "stop": (0.0, 0.0),
}

COMPOUND_BASE_SPEED = 0.6

SKILL_NAMES = ["forward", "backward", "left", "right", "stop", "spin", "wiggle", "dance"]
NUM_SKILLS = len(SKILL_NAMES)

# Clamp ranges (same as conversation.py)
MIN_SPEED = 0.1
MAX_SPEED = 1.0
MIN_DURATION = 0.1
MAX_DURATION = 5.0


def _clamp(val: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, val))


def execute_skill(
    sim: Simulator,
    skill_index: int,
    speed: float,
    duration: float,
    sim_dt: float = 0.02,
) -> list[tuple[float, float, float]]:
    """Execute a skill on *sim* and return the trajectory [(x, y, heading), ...].

    Parameters are clamped to valid ranges.
    """
    skill_index = _clamp(skill_index, 0, NUM_SKILLS - 1)
    speed = _clamp(speed, MIN_SPEED, MAX_SPEED)
    duration = _clamp(duration, MIN_DURATION, MAX_DURATION)

    name = SKILL_NAMES[int(skill_index)]

    if name in MOVE_PRESETS:
        return _execute_simple(sim, name, speed, duration, sim_dt)
    elif name == "spin":
        return _execute_spin(sim, speed, duration, sim_dt)
    elif name == "wiggle":
        return _execute_wiggle(sim, speed, duration, sim_dt)
    elif name == "dance":
        return _execute_dance(sim, speed, duration, sim_dt)
    return []


def _execute_simple(
    sim: Simulator, name: str, speed: float, duration: float, dt: float
) -> list[tuple[float, float, float]]:
    base_l, base_r = MOVE_PRESETS[name]
    left = _clamp(base_l * speed, -1.0, 1.0)
    right = _clamp(base_r * speed, -1.0, 1.0)
    sim.set_motors(left, right)
    traj = sim.run_for(duration, dt)
    sim.set_motors(0, 0)
    return traj


def _execute_spin(
    sim: Simulator, speed: float, duration: float, dt: float
) -> list[tuple[float, float, float]]:
    spd = _clamp(COMPOUND_BASE_SPEED * speed, -1.0, 1.0)
    sim.set_motors(spd, -spd)
    traj = sim.run_for(duration, dt)
    sim.set_motors(0, 0)
    return traj


def _execute_wiggle(
    sim: Simulator, speed: float, duration: float, dt: float
) -> list[tuple[float, float, float]]:
    step = 0.2
    spd = _clamp(COMPOUND_BASE_SPEED * speed, -1.0, 1.0)
    trajectory: list[tuple[float, float, float]] = []
    elapsed = 0.0
    go_left = True
    while elapsed < duration:
        t = min(step, duration - elapsed)
        if go_left:
            sim.set_motors(-spd, spd)
        else:
            sim.set_motors(spd, -spd)
        trajectory.extend(sim.run_for(t, dt))
        elapsed += t
        go_left = not go_left
    sim.set_motors(0, 0)
    return trajectory


def _execute_dance(
    sim: Simulator, speed: float, duration: float, dt: float
) -> list[tuple[float, float, float]]:
    quarter = duration / 4.0
    trajectory: list[tuple[float, float, float]] = []
    trajectory.extend(_execute_simple(sim, "forward", speed, quarter, dt))
    trajectory.extend(_execute_spin(sim, speed, quarter, dt))
    trajectory.extend(_execute_wiggle(sim, speed, quarter, dt))
    trajectory.extend(_execute_simple(sim, "backward", speed, quarter, dt))
    return trajectory
