"""Tests for the async event bus."""

import pytest
from emiglio.event_bus import EventBus


async def test_publish_calls_handler(bus: EventBus):
    received = []

    async def handler(data):
        received.append(data)

    bus.subscribe("test.event", handler)
    await bus.publish("test.event", {"key": "value"})

    assert len(received) == 1
    assert received[0] == {"key": "value"}


async def test_multiple_handlers(bus: EventBus):
    results = []

    async def handler_a(data):
        results.append("a")

    async def handler_b(data):
        results.append("b")

    bus.subscribe("test.event", handler_a)
    bus.subscribe("test.event", handler_b)
    await bus.publish("test.event", None)

    assert sorted(results) == ["a", "b"]


async def test_publish_no_handlers(bus: EventBus):
    # Should not raise
    await bus.publish("nonexistent.event", "data")


async def test_unsubscribe(bus: EventBus):
    received = []

    async def handler(data):
        received.append(data)

    bus.subscribe("test.event", handler)
    bus.unsubscribe("test.event", handler)
    await bus.publish("test.event", "data")

    assert len(received) == 0


async def test_handler_error_does_not_break_others(bus: EventBus):
    results = []

    async def bad_handler(data):
        raise ValueError("boom")

    async def good_handler(data):
        results.append(data)

    bus.subscribe("test.event", bad_handler)
    bus.subscribe("test.event", good_handler)
    await bus.publish("test.event", "hello")

    assert results == ["hello"]
