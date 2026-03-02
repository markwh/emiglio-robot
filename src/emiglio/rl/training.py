"""RL training manager — bridges SB3 PPO with the asyncio web server."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

from emiglio.rl.env import EmiglioNavEnv
from emiglio.rl.nav_env import PatrolNavEnv, NAV_SKILLS, NAV_NUM_SKILLS
from emiglio.rl.skills import SKILL_NAMES, NUM_SKILLS

logger = logging.getLogger(__name__)

# How often to print diagnostic summaries
_LOG_INTERVAL = 50

# Default models directory at project root
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MODELS_DIR = _PROJECT_ROOT / "models"


@dataclass
class ModelMetadata:
    """Metadata saved alongside a trained model."""
    name: str
    timestamp: float
    total_timesteps: int
    episodes: int
    mean_reward: float
    goal_rate: float
    learning_rate: float
    randomization_strength: float
    env_type: str = "legacy"

    def save(self, path: Path) -> None:
        path.write_text(json.dumps(self.__dict__, indent=2))

    @classmethod
    def load(cls, path: Path) -> ModelMetadata:
        return cls(**json.loads(path.read_text()))


@dataclass
class TrainingStats:
    """Per-episode statistics pushed to the UI."""
    episode: int
    reward: float
    length: int
    goal_reached: bool
    dist_to_goal: float


@dataclass
class TrainingEpisode:
    """Stats + trajectory for replay (sent every *demo_interval* episodes)."""
    stats: TrainingStats
    trajectory: list[tuple[float, float, float]]
    goal: tuple[float, float]


class WebSocketCallback(BaseCallback):
    """SB3 callback that pushes training data to an asyncio queue."""

    def __init__(
        self,
        queue: asyncio.Queue,
        loop: asyncio.AbstractEventLoop,
        demo_interval_ref: list[int],
        stop_flag: list[bool],
        env_type: str = "legacy",
    ) -> None:
        super().__init__()
        self.queue = queue
        self.loop = loop
        self._demo_interval_ref = demo_interval_ref
        self.stop_flag = stop_flag
        self._env_type = env_type

        # Skill names depend on env type
        if env_type == "nav":
            self._skill_names = NAV_SKILLS
            self._num_skills = NAV_NUM_SKILLS
        else:
            self._skill_names = SKILL_NAMES
            self._num_skills = NUM_SKILLS

        self._episode_count = 0
        self._episode_reward = 0.0
        self._episode_steps = 0

        # Cumulative counters for metadata on save
        self.total_episodes = 0
        self.total_reward = 0.0
        self.total_goals = 0

        # Rolling window for diagnostic logging
        self._recent_rewards: list[float] = []
        self._recent_dists: list[float] = []
        self._recent_goals: list[bool] = []
        self._recent_skill_counts: list[int] = [0] * self._num_skills
        self._recent_wall_hits = 0
        self._recent_steps: list[int] = []

    def _on_step(self) -> bool:
        if self.stop_flag[0]:
            return False

        self._episode_reward += self.locals["rewards"][0]
        self._episode_steps += 1

        done = self.locals["dones"][0]
        if done:
            self._episode_count += 1
            self.total_episodes += 1
            info = self.locals["infos"][0]

            ep_reward = info.get("episode_reward", self._episode_reward)
            goal_reached = info.get("goal_reached", False)
            dist = info.get("dist_to_goal", -1.0)
            self.total_reward += ep_reward
            if goal_reached:
                self.total_goals += 1

            # Accumulate rolling diagnostics
            self._recent_rewards.append(ep_reward)
            self._recent_dists.append(dist)
            self._recent_goals.append(goal_reached)
            self._recent_steps.append(self._episode_steps)
            skill_counts = info.get("skill_counts")
            if skill_counts:
                for i, c in enumerate(skill_counts):
                    self._recent_skill_counts[i] += c
            self._recent_wall_hits += info.get("wall_hits", 0)

            # Periodic diagnostic log
            if self._episode_count % _LOG_INTERVAL == 0 and self._recent_rewards:
                n = len(self._recent_rewards)
                mean_r = sum(self._recent_rewards) / n
                mean_d = sum(self._recent_dists) / n
                goal_pct = sum(self._recent_goals) / n * 100
                mean_steps = sum(self._recent_steps) / n
                total_skills = sum(self._recent_skill_counts) or 1
                skill_dist = "  ".join(
                    f"{self._skill_names[i]}={self._recent_skill_counts[i]/total_skills*100:.0f}%"
                    for i in range(self._num_skills)
                    if self._recent_skill_counts[i] > 0
                )
                logger.info(
                    "EP %d | last %d: reward=%.2f  dist=%.0f  goals=%.0f%%  steps=%.1f  walls=%d | skills: %s",
                    self._episode_count, n, mean_r, mean_d, goal_pct,
                    mean_steps, self._recent_wall_hits, skill_dist,
                )
                # Reset rolling window
                self._recent_rewards.clear()
                self._recent_dists.clear()
                self._recent_goals.clear()
                self._recent_steps.clear()
                self._recent_skill_counts = [0] * self._num_skills
                self._recent_wall_hits = 0

            stats = TrainingStats(
                episode=self._episode_count,
                reward=ep_reward,
                length=self._episode_steps,
                goal_reached=goal_reached,
                dist_to_goal=info.get("dist_to_goal", -1.0),
            )

            interval = max(1, self._demo_interval_ref[0])
            is_demo = (self._episode_count % interval) == 0

            if is_demo and "episode_trajectory" in info:
                traj = info["episode_trajectory"]
                goal = info.get("episode_goal", (0, 0))
                item = TrainingEpisode(stats=stats, trajectory=traj, goal=goal)
            else:
                item = stats

            self.loop.call_soon_threadsafe(self.queue.put_nowait, item)

            self._episode_reward = 0.0
            self._episode_steps = 0

        return True


class TrainingManager:
    """Manages an SB3 PPO training run in a background thread."""

    def __init__(self, models_dir: Path | None = None) -> None:
        self.queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self._stop_flag: list[bool] = [False]
        self._demo_interval: list[int] = [1]
        self._task: asyncio.Task | None = None
        self.models_dir = models_dir or DEFAULT_MODELS_DIR

        # Mutable refs accessible from training thread
        self._model_ref: list[PPO | None] = [None]
        self._callback_ref: list[WebSocketCallback | None] = [None]
        self._current_config: dict = {}

    async def start_training(
        self,
        total_timesteps: int = 100_000,
        demo_interval: int = 1,
        learning_rate: float = 3e-4,
        randomization_strength: float = 0.0,
        resume_from: str | None = None,
        env_type: str = "legacy",
    ) -> None:
        if self.running:
            logger.warning("Training already running")
            return

        self.running = True
        self._stop_flag[0] = False
        self._demo_interval[0] = demo_interval
        self._current_config = {
            "total_timesteps": total_timesteps,
            "learning_rate": learning_rate,
            "randomization_strength": randomization_strength,
            "env_type": env_type,
        }

        # Drain any stale items
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        loop = asyncio.get_running_loop()

        # Resolve resume path
        resume_path: str | None = None
        if resume_from:
            p = self.models_dir / resume_from / "model.zip"
            if p.exists():
                resume_path = str(p.with_suffix(""))  # SB3 wants path without .zip
            else:
                logger.warning("Resume model not found: %s", p)

        def _train() -> None:
            if env_type == "nav":
                env = PatrolNavEnv()
                logger.info("Training with PatrolNavEnv (4 nav skills, 8D obs)")
            else:
                env = EmiglioNavEnv(randomization_strength=randomization_strength)
                logger.info("Training with EmiglioNavEnv (8 skills, 6D obs)")

            if resume_path:
                model = PPO.load(resume_path, env=env)
                model.learning_rate = learning_rate
            else:
                model = PPO(
                    "MlpPolicy",
                    env,
                    n_steps=2048,
                    batch_size=64,
                    n_epochs=10,
                    learning_rate=learning_rate,
                    verbose=0,
                )

            self._model_ref[0] = model

            callback = WebSocketCallback(
                queue=self.queue,
                loop=loop,
                demo_interval_ref=self._demo_interval,
                stop_flag=self._stop_flag,
                env_type=env_type,
            )
            self._callback_ref[0] = callback

            try:
                model.learn(total_timesteps=total_timesteps, callback=callback)
            except Exception:
                logger.exception("Training error")
            finally:
                # Auto-save on stop
                try:
                    name = f"auto_{int(time.time())}"
                    self._save_model(name, callback)
                    logger.info("Auto-saved model as %s", name)
                except Exception:
                    logger.exception("Auto-save failed")
                loop.call_soon_threadsafe(self.queue.put_nowait, None)  # sentinel

        self._task = asyncio.ensure_future(asyncio.to_thread(_train))

        def _on_done(fut: asyncio.Future) -> None:
            self.running = False
            self._model_ref[0] = None
            self._callback_ref[0] = None
            logger.info("Training finished")

        self._task.add_done_callback(_on_done)

    def stop_training(self) -> None:
        self._stop_flag[0] = True

    def set_demo_interval(self, interval: int) -> None:
        """Live update of demo_interval via shared mutable list."""
        self._demo_interval[0] = max(1, interval)

    def _save_model(self, name: str, callback: WebSocketCallback) -> Path:
        """Save model + metadata to disk. Called from training thread."""
        model = self._model_ref[0]
        if model is None:
            raise RuntimeError("No model to save")

        model_dir = self.models_dir / name
        model_dir.mkdir(parents=True, exist_ok=True)
        model.save(str(model_dir / "model"))

        total_ep = callback.total_episodes or 1
        meta = ModelMetadata(
            name=name,
            timestamp=time.time(),
            total_timesteps=self._current_config.get("total_timesteps", 0),
            episodes=callback.total_episodes,
            mean_reward=callback.total_reward / total_ep,
            goal_rate=callback.total_goals / total_ep,
            learning_rate=self._current_config.get("learning_rate", 3e-4),
            randomization_strength=self._current_config.get("randomization_strength", 0.0),
            env_type=self._current_config.get("env_type", "legacy"),
        )
        meta.save(model_dir / "metadata.json")
        return model_dir

    def save_current(self, name: str) -> str | None:
        """Explicit save from WS handler. Returns model name or None."""
        model = self._model_ref[0]
        callback = self._callback_ref[0]
        if model is None or callback is None:
            return None
        try:
            self._save_model(name, callback)
            return name
        except Exception:
            logger.exception("save_current failed")
            return None

    def list_models(self) -> list[dict]:
        """Scan models directory for saved models."""
        if not self.models_dir.exists():
            return []
        results = []
        for meta_path in sorted(self.models_dir.glob("*/metadata.json")):
            try:
                meta = ModelMetadata.load(meta_path)
                results.append(meta.__dict__)
            except Exception:
                logger.warning("Skipping invalid metadata: %s", meta_path)
        return results

    async def run_inference(self, model_name: str, num_episodes: int = 5) -> None:
        """Load a model and run deterministic episodes, pushing replays to queue."""
        model_path = self.models_dir / model_name / "model.zip"
        if not model_path.exists():
            logger.warning("Inference model not found: %s", model_path)
            return

        loop = asyncio.get_running_loop()
        queue = self.queue

        def _infer() -> None:
            # Auto-detect env type from model observation space
            model = PPO.load(str(model_path.with_suffix("")))
            obs_dim = model.observation_space.shape[0]
            if obs_dim == 8:
                env = PatrolNavEnv()
                logger.info("Inference: detected nav-format model (8D obs)")
            else:
                env = EmiglioNavEnv()
                logger.info("Inference: detected legacy-format model (6D obs)")
            model.set_env(env)

            for ep in range(num_episodes):
                obs, _ = env.reset()
                done = False
                while not done:
                    action, _ = model.predict(obs, deterministic=True)
                    obs, reward, terminated, truncated, info = env.step(action)
                    done = terminated or truncated

                if "episode_trajectory" in info:
                    stats = TrainingStats(
                        episode=ep + 1,
                        reward=info.get("episode_reward", 0.0),
                        length=len(info["episode_trajectory"]),
                        goal_reached=info.get("goal_reached", False),
                        dist_to_goal=info.get("dist_to_goal", -1.0),
                    )
                    item = TrainingEpisode(
                        stats=stats,
                        trajectory=info["episode_trajectory"],
                        goal=info.get("episode_goal", (0, 0)),
                    )
                    loop.call_soon_threadsafe(queue.put_nowait, item)

                # Pace between episodes
                if ep < num_episodes - 1:
                    import time as _time
                    _time.sleep(0.3)

            loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        asyncio.ensure_future(asyncio.to_thread(_infer))
