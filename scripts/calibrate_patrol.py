#!/usr/bin/env python3
"""Calibrate the RL policy on the patrol-square skill.

Trains in short rounds, evaluates patrol waypoint navigation after each round,
and prints geometric metrics so you can iterate quickly.

Usage:
    uv run python scripts/calibrate_patrol.py                  # fresh start
    uv run python scripts/calibrate_patrol.py --resume patrol  # resume from saved model
    uv run python scripts/calibrate_patrol.py --eval-only patrol  # evaluate only, no training
"""

from __future__ import annotations

import argparse
import math
import sys
import time
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from emiglio.rl.env import EmiglioNavEnv
from emiglio.rl.nav_env import PatrolNavEnv, NAV_SKILLS, NAV_NUM_SKILLS, _NAV_TO_FULL
from emiglio.rl.sim import SIM_SIZE, MARGIN, Simulator, SimConfig, randomized_config
from emiglio.rl.skills import SKILL_NAMES, NUM_SKILLS, execute_skill
from emiglio.rl.waypoints import patrol_waypoints

MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
GOAL_RADIUS = 30.0
MAX_STEPS_PER_WP = 30


# ---------------------------------------------------------------------------
# Evaluation: run patrol waypoints through the sim using policy predictions
# ---------------------------------------------------------------------------

def evaluate_patrol(
    model,
    duration: float = 4.0,
    n_trials: int = 5,
    verbose: bool = True,
) -> dict:
    """Run the patrol waypoint sequence n_trials times, return metrics."""
    waypoints = patrol_waypoints(duration=duration)

    if verbose:
        print(f"\n  Patrol waypoints (duration={duration}s):")
        for i, (wx, wy) in enumerate(waypoints):
            print(f"    WP{i}: ({wx:.0f}, {wy:.0f})")

    trial_results = []
    for trial in range(n_trials):
        sim = Simulator(SimConfig())
        wp_results = []

        for wi, (gx, gy) in enumerate(waypoints):
            reached, final_dist, steps, skills_used = _navigate_to_wp(
                model, sim, (gx, gy),
            )
            wp_results.append({
                "waypoint": (gx, gy),
                "reached": reached,
                "final_dist": final_dist,
                "final_pos": (sim.state.x, sim.state.y),
                "steps": steps,
                "skills": skills_used,
            })

        all_reached = all(r["reached"] for r in wp_results)
        mean_dist = np.mean([r["final_dist"] for r in wp_results])
        trial_results.append({
            "all_reached": all_reached,
            "mean_dist": mean_dist,
            "waypoints": wp_results,
        })

    # Aggregate
    n_complete = sum(t["all_reached"] for t in trial_results)
    overall_mean_dist = np.mean([t["mean_dist"] for t in trial_results])

    # Per-waypoint stats
    n_wps = len(waypoints)
    wp_reach_rates = []
    wp_mean_dists = []
    for wi in range(n_wps):
        reached_count = sum(
            t["waypoints"][wi]["reached"] for t in trial_results
        )
        mean_d = np.mean(
            [t["waypoints"][wi]["final_dist"] for t in trial_results]
        )
        wp_reach_rates.append(reached_count / n_trials)
        wp_mean_dists.append(mean_d)

    # Shape quality: measure the actual square formed by final positions
    # Use the last trial for geometric analysis
    last_trial = trial_results[-1]
    actual_positions = [r["final_pos"] for r in last_trial["waypoints"]]
    shape_metrics = _measure_square_quality(waypoints, actual_positions)

    result = {
        "complete_rate": n_complete / n_trials,
        "overall_mean_dist": overall_mean_dist,
        "wp_reach_rates": wp_reach_rates,
        "wp_mean_dists": wp_mean_dists,
        "shape": shape_metrics,
        "trials": trial_results,
    }

    if verbose:
        _print_eval_report(result, n_trials)

    return result


def _navigate_to_wp(
    model, sim: Simulator, goal: tuple[float, float],
) -> tuple[bool, float, int, dict[str, int]]:
    """Navigate sim to a single goal using policy. Returns (reached, dist, steps, skill_counts)."""
    skills_used: dict[str, int] = {}
    diag = math.hypot(SIM_SIZE, SIM_SIZE)

    for step in range(MAX_STEPS_PER_WP):
        dist = math.hypot(sim.state.x - goal[0], sim.state.y - goal[1])
        if dist <= GOAL_RADIUS:
            return True, dist, step, skills_used

        # Build obs matching PatrolNavEnv._get_obs()
        s = sim.state
        dx = goal[0] - s.x
        dy = goal[1] - s.y
        goal_angle = math.atan2(dy, dx)
        rel_bearing = goal_angle - s.heading
        obs = np.array([
            s.x / SIM_SIZE * 2 - 1,
            s.y / SIM_SIZE * 2 - 1,
            math.sin(s.heading),
            math.cos(s.heading),
            dist / diag * 2 - 1,
            math.sin(rel_bearing),
            math.cos(rel_bearing),
            1.0 if dist < 60 else -1.0,
        ], dtype=np.float32)

        action, _ = model.predict(obs, deterministic=True)
        nav_idx = min(int(action[0] * NAV_NUM_SKILLS), NAV_NUM_SKILLS - 1)
        full_idx = _NAV_TO_FULL[nav_idx]
        speed = float(action[1])
        duration = float(action[2])

        skill_name = NAV_SKILLS[nav_idx]
        skills_used[skill_name] = skills_used.get(skill_name, 0) + 1
        execute_skill(sim, full_idx, speed, duration)

    final_dist = math.hypot(sim.state.x - goal[0], sim.state.y - goal[1])
    return final_dist <= GOAL_RADIUS, final_dist, MAX_STEPS_PER_WP, skills_used


def _measure_square_quality(
    target_pts: list[tuple[float, float]],
    actual_pts: list[tuple[float, float]],
) -> dict:
    """Measure how well the actual positions form the intended square."""
    # Per-vertex error
    vertex_errors = [
        math.hypot(a[0] - t[0], a[1] - t[1])
        for t, a in zip(target_pts, actual_pts)
    ]

    # Side lengths of actual shape
    n = len(actual_pts)
    actual_sides = []
    for i in range(n):
        j = (i + 1) % n
        actual_sides.append(math.hypot(
            actual_pts[j][0] - actual_pts[i][0],
            actual_pts[j][1] - actual_pts[i][1],
        ))

    # Target side lengths
    target_sides = []
    for i in range(n):
        j = (i + 1) % n
        target_sides.append(math.hypot(
            target_pts[j][0] - target_pts[i][0],
            target_pts[j][1] - target_pts[i][1],
        ))

    # Side length error ratio
    side_errors = [
        abs(a - t) / t if t > 0 else 0
        for t, a in zip(target_sides, actual_sides)
    ]

    return {
        "vertex_errors": vertex_errors,
        "mean_vertex_error": np.mean(vertex_errors),
        "actual_sides": actual_sides,
        "target_sides": target_sides,
        "side_errors": side_errors,
        "mean_side_error": np.mean(side_errors),
    }


def _print_eval_report(result: dict, n_trials: int) -> None:
    """Print a formatted evaluation report."""
    print(f"\n{'='*60}")
    print(f"  PATROL EVALUATION ({n_trials} trials)")
    print(f"{'='*60}")

    cr = result["complete_rate"]
    status = "PASS" if cr >= 0.8 else "IMPROVING" if cr > 0 else "FAIL"
    print(f"  Complete squares: {cr*100:.0f}%  [{status}]")
    print(f"  Mean dist to waypoint: {result['overall_mean_dist']:.1f}px")

    print(f"\n  Per-waypoint breakdown:")
    for i, (rate, dist) in enumerate(zip(
        result["wp_reach_rates"], result["wp_mean_dists"],
    )):
        marker = "OK" if rate >= 0.8 else "MISS"
        print(f"    WP{i}: reach={rate*100:.0f}%  mean_dist={dist:.1f}px  [{marker}]")

    shape = result["shape"]
    print(f"\n  Square geometry (last trial):")
    print(f"    Mean vertex error: {shape['mean_vertex_error']:.1f}px")
    for i, (ve, ts, asid, se) in enumerate(zip(
        shape["vertex_errors"],
        shape["target_sides"],
        shape["actual_sides"],
        shape["side_errors"],
    )):
        print(f"    Side {i}→{(i+1)%4}: target={ts:.0f}px  actual={asid:.0f}px  err={se*100:.0f}%  vertex_err={ve:.1f}px")

    # Skill distribution from last trial
    all_skills: dict[str, int] = {}
    for wp_r in result["trials"][-1]["waypoints"]:
        for sk, cnt in wp_r["skills"].items():
            all_skills[sk] = all_skills.get(sk, 0) + cnt
    total = sum(all_skills.values()) or 1
    skill_str = "  ".join(
        f"{k}={v/total*100:.0f}%"
        for k, v in sorted(all_skills.items(), key=lambda x: -x[1])
    )
    print(f"\n  Skill usage: {skill_str}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_round(
    model,
    env: EmiglioNavEnv,
    timesteps: int = 20_000,
) -> None:
    """Train for one round of timesteps."""
    model.learn(total_timesteps=timesteps, reset_num_timesteps=False)


def main():
    parser = argparse.ArgumentParser(description="Calibrate RL patrol-square skill")
    parser.add_argument("--resume", type=str, default=None,
                        help="Resume from saved model name")
    parser.add_argument("--eval-only", type=str, default=None,
                        help="Evaluate a saved model without training")
    parser.add_argument("--rounds", type=int, default=10,
                        help="Number of training rounds (default: 10)")
    parser.add_argument("--timesteps", type=int, default=20_000,
                        help="Timesteps per round (default: 20000)")
    parser.add_argument("--lr", type=float, default=3e-4,
                        help="Learning rate (default: 3e-4)")
    parser.add_argument("--trials", type=int, default=5,
                        help="Evaluation trials per round (default: 5)")
    parser.add_argument("--save-name", type=str, default="patrol",
                        help="Model save name (default: patrol)")
    args = parser.parse_args()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Eval-only mode
    if args.eval_only:
        model_path = MODELS_DIR / args.eval_only / "model.zip"
        if not model_path.exists():
            print(f"Model not found: {model_path}")
            sys.exit(1)
        print(f"Evaluating model: {args.eval_only}")
        model = PPO.load(str(model_path.with_suffix("")))
        evaluate_patrol(model, n_trials=args.trials)
        return

    # Nav-focused env: 4 skills, richer obs, tuned reward
    env = PatrolNavEnv(
        max_steps=40,
        goal_radius=GOAL_RADIUS,
        min_goal_dist=50.0,
    )

    # Create or load model
    if args.resume:
        model_path = MODELS_DIR / args.resume / "model.zip"
        if not model_path.exists():
            print(f"Model not found: {model_path}")
            sys.exit(1)
        print(f"Resuming from {model_path}")
        model = PPO.load(str(model_path.with_suffix("")), env=env)
        model.learning_rate = args.lr
    else:
        print("Starting fresh model")
        model = PPO(
            "MlpPolicy", env,
            n_steps=2048,
            batch_size=64,
            n_epochs=10,
            learning_rate=args.lr,
            verbose=0,
        )

    print(f"Training: {args.rounds} rounds × {args.timesteps} timesteps = {args.rounds * args.timesteps} total")
    print(f"Learning rate: {args.lr}")
    print(f"Env: PatrolNavEnv (4 nav skills, relative bearing obs, tuned reward)")
    print(f"Eval trials per round: {args.trials}")

    best_complete_rate = 0.0
    start_time = time.time()

    for rnd in range(1, args.rounds + 1):
        t0 = time.time()
        train_round(model, env, timesteps=args.timesteps)
        train_time = time.time() - t0

        print(f"\n--- Round {rnd}/{args.rounds} ({args.timesteps} steps in {train_time:.1f}s) ---")

        result = evaluate_patrol(model, n_trials=args.trials)

        cr = result["complete_rate"]
        if cr > best_complete_rate:
            best_complete_rate = cr
            # Save improved model
            save_dir = MODELS_DIR / args.save_name
            save_dir.mkdir(parents=True, exist_ok=True)
            model.save(str(save_dir / "model"))
            print(f"  ** Saved improved model ({cr*100:.0f}% complete) → {save_dir}")

        mean_ve = result["shape"]["mean_vertex_error"]
        if cr >= 1.0 and mean_ve < 12.0:
            print(f"\n  All trials complete with tight geometry ({mean_ve:.1f}px)! Stopping early.")
            break

    elapsed = time.time() - start_time
    print(f"\nDone in {elapsed:.0f}s. Best complete rate: {best_complete_rate*100:.0f}%")
    print(f"Model saved at: {MODELS_DIR / args.save_name}")


if __name__ == "__main__":
    main()
