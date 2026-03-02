"""RL training manager — bridges SB3 PPO with the asyncio web server."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

from emiglio.rl.env import EmiglioNavEnv

logger = logging.getLogger(__name__)


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
    ) -> None:
        super().__init__()
        self.queue = queue
        self.loop = loop
        self._demo_interval_ref = demo_interval_ref
        self.stop_flag = stop_flag

        self._episode_count = 0
        self._episode_reward = 0.0
        self._episode_steps = 0

    def _on_step(self) -> bool:
        if self.stop_flag[0]:
            return False

        self._episode_reward += self.locals["rewards"][0]
        self._episode_steps += 1

        done = self.locals["dones"][0]
        if done:
            self._episode_count += 1
            info = self.locals["infos"][0]

            stats = TrainingStats(
                episode=self._episode_count,
                reward=info.get("episode_reward", self._episode_reward),
                length=self._episode_steps,
                goal_reached=info.get("goal_reached", False),
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

    def __init__(self) -> None:
        self.queue: asyncio.Queue = asyncio.Queue()
        self.running = False
        self._stop_flag: list[bool] = [False]
        self._demo_interval: list[int] = [1]
        self._task: asyncio.Task | None = None

    async def start_training(
        self,
        total_timesteps: int = 100_000,
        demo_interval: int = 1,
        learning_rate: float = 3e-4,
    ) -> None:
        if self.running:
            logger.warning("Training already running")
            return

        self.running = True
        self._stop_flag[0] = False
        self._demo_interval[0] = demo_interval

        # Drain any stale items
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except asyncio.QueueEmpty:
                break

        loop = asyncio.get_running_loop()

        def _train() -> None:
            env = EmiglioNavEnv()
            model = PPO(
                "MlpPolicy",
                env,
                n_steps=2048,
                batch_size=64,
                n_epochs=10,
                learning_rate=learning_rate,
                verbose=0,
            )
            callback = WebSocketCallback(
                queue=self.queue,
                loop=loop,
                demo_interval_ref=self._demo_interval,
                stop_flag=self._stop_flag,
            )
            try:
                model.learn(total_timesteps=total_timesteps, callback=callback)
            except Exception:
                logger.exception("Training error")
            finally:
                loop.call_soon_threadsafe(self.queue.put_nowait, None)  # sentinel

        self._task = asyncio.ensure_future(asyncio.to_thread(_train))

        def _on_done(fut: asyncio.Future) -> None:
            self.running = False
            logger.info("Training finished")

        self._task.add_done_callback(_on_done)

    def stop_training(self) -> None:
        self._stop_flag[0] = True

    def set_demo_interval(self, interval: int) -> None:
        """Live update of demo_interval via shared mutable list."""
        self._demo_interval[0] = max(1, interval)
