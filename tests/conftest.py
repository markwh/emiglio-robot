"""Shared test fixtures."""

import os
import pytest
from emiglio.event_bus import EventBus

# Force mock mode for all tests
os.environ["EMIGLIO_HARDWARE_MODE"] = "mock"


@pytest.fixture
def bus():
    return EventBus()
