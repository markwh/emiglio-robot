"""Async pub/sub event bus for inter-subsystem communication."""

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

Handler = Callable[..., Coroutine[Any, Any, None]]


class EventBus:
    """Simple async event bus. Subsystems publish and subscribe to named events."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Handler) -> None:
        """Register an async handler for an event type."""
        self._handlers[event_type].append(handler)
        logger.debug("Subscribed %s to '%s'", handler.__qualname__, event_type)

    def unsubscribe(self, event_type: str, handler: Handler) -> None:
        """Remove a handler from an event type."""
        self._handlers[event_type].remove(handler)

    async def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event, calling all subscribed handlers concurrently."""
        handlers = self._handlers.get(event_type, [])
        if not handlers:
            return
        logger.debug("Publishing '%s' to %d handler(s)", event_type, len(handlers))
        results = await asyncio.gather(
            *(h(data) for h in handlers), return_exceptions=True
        )
        for result in results:
            if isinstance(result, Exception):
                logger.error(
                    "Handler error on '%s': %s", event_type, result, exc_info=result
                )
