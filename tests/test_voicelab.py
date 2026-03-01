"""Tests for Voice Lab API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from emiglio.event_bus import EventBus
from emiglio.locomotion.controller import LocomotionController
from emiglio.web.server import create_app


def _make_app_with_tts(tts_mock):
    """Create a FastAPI app with a mocked ConversationManager holding the given TTS mock."""
    bus = EventBus()
    locomotion = LocomotionController(bus)
    conversation = MagicMock()
    conversation._tts = tts_mock
    conversation._capture = None
    conversation._playback = None
    conversation.busy = False
    return create_app(bus, locomotion, conversation=conversation)


def _make_tts_mock(voice_id="21m00Tcm4TlvDq8ikWAM"):
    """Create a mock TTSClient."""
    tts = MagicMock()
    tts.available = True
    tts.voice_id = voice_id
    tts.model_id = "eleven_flash_v2_5"
    tts.list_voices = AsyncMock(return_value=[
        {
            "voice_id": "v1",
            "name": "Rachel",
            "category": "premade",
            "labels": {"accent": "american"},
            "description": "Calm voice",
            "preview_url": "https://example.com/preview.mp3",
        },
        {
            "voice_id": "v2",
            "name": "Dave",
            "category": "cloned",
            "labels": {},
            "description": "",
            "preview_url": "",
        },
    ])
    tts.set_voice = MagicMock()
    tts.synthesize = AsyncMock(return_value=b"RIFF\x00\x00\x00\x00WAVEfmt fake")
    return tts


async def test_voicelab_voices():
    """GET /voicelab/voices returns voice list and active_voice_id."""
    tts = _make_tts_mock(voice_id="v1")
    app = _make_app_with_tts(tts)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/voicelab/voices")

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert len(data["voices"]) == 2
    assert data["voices"][0]["voice_id"] == "v1"
    assert data["voices"][1]["name"] == "Dave"
    assert data["active_voice_id"] == "v1"
    tts.list_voices.assert_awaited_once()


async def test_voicelab_preview():
    """POST /voicelab/preview returns audio/wav bytes."""
    tts = _make_tts_mock()
    app = _make_app_with_tts(tts)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/voicelab/preview",
            json={"text": "Hello robot", "voice_id": "v1"},
        )

    assert resp.status_code == 200
    assert resp.headers["content-type"] == "audio/wav"
    assert resp.content == b"RIFF\x00\x00\x00\x00WAVEfmt fake"
    tts.synthesize.assert_awaited_once_with(text="Hello robot", voice_id="v1", model_id=None)


async def test_voicelab_activate():
    """POST /voicelab/activate calls set_voice and returns ok."""
    tts = _make_tts_mock(voice_id="v1")
    # After set_voice is called, voice_id property should reflect the new value
    type(tts).voice_id = property(lambda self: "v2")
    tts.set_voice = MagicMock()
    app = _make_app_with_tts(tts)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/voicelab/activate",
            json={"voice_id": "v2"},
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["active_voice_id"] == "v2"
    tts.set_voice.assert_called_once_with("v2")


async def test_voicelab_voices_no_tts():
    """GET /voicelab/voices returns error when TTS is unavailable."""
    bus = EventBus()
    locomotion = LocomotionController(bus)
    app = create_app(bus, locomotion, conversation=None)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/voicelab/voices")

    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is False
    assert "not available" in data["error"]
