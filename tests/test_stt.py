"""Tests for the STT client (ElevenLabs, inline Whisper, and server modes)."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from emiglio.stt import STTClient


def _make_mock_whisper(mock_model=None):
    """Create a mock whisper module and inject into sys.modules."""
    mock_whisper = MagicMock()
    mock_whisper.load_model.return_value = mock_model or MagicMock()
    return mock_whisper


# --- ElevenLabs mode ---


def test_stt_client_elevenlabs_mode():
    """STTClient in elevenlabs mode creates an HTTP client when key is provided."""
    client = STTClient(mode="elevenlabs", elevenlabs_api_key="test-key")
    assert client._mode == "elevenlabs"
    assert client.available is True
    assert client._http is not None


def test_stt_client_elevenlabs_no_key():
    """STTClient in elevenlabs mode without key is not available."""
    client = STTClient(mode="elevenlabs", elevenlabs_api_key="")
    assert client.available is False


async def test_transcribe_elevenlabs():
    """ElevenLabs transcription POSTs to the Scribe API."""
    client = STTClient(
        mode="elevenlabs", elevenlabs_api_key="test-key", elevenlabs_model="scribe_v2"
    )

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"text": " Hello from ElevenLabs "}
    mock_resp.raise_for_status = MagicMock()

    client._http.post = AsyncMock(return_value=mock_resp)
    wav_bytes = b"RIFF\x00\x00\x00\x00WAVEfmt fake wav data"
    result = await client.transcribe(wav_bytes)

    assert result == "Hello from ElevenLabs"
    client._http.post.assert_called_once()

    call_args = client._http.post.call_args
    assert "speech-to-text" in call_args[0][0]
    assert call_args[1]["headers"]["xi-api-key"] == "test-key"
    assert call_args[1]["data"]["model_id"] == "scribe_v2"


# --- Inline Whisper mode ---


def test_stt_client_inline_mode():
    """STTClient in inline mode loads a Whisper model (or warns if unavailable)."""
    mock_whisper = _make_mock_whisper()
    with patch.dict(sys.modules, {"whisper": mock_whisper}):
        client = STTClient(mode="inline", model="base")
    assert client._mode == "inline"
    assert client.available is True
    mock_whisper.load_model.assert_called_once_with("base")


async def test_transcribe_inline():
    """Inline transcription writes WAV to tempfile and calls whisper.transcribe."""
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": " Hello, world! "}

    mock_whisper = _make_mock_whisper(mock_model)
    with patch.dict(sys.modules, {"whisper": mock_whisper}):
        client = STTClient(mode="inline", model="base", language="en")

    wav_bytes = b"RIFF\x00\x00\x00\x00WAVEfmt fake wav data"
    result = await client.transcribe(wav_bytes)

    assert result == "Hello, world!"
    mock_model.transcribe.assert_called_once()
    call_args = mock_model.transcribe.call_args
    assert call_args[0][0].endswith(".wav")
    assert call_args[1]["language"] == "en"
    assert "Emiglio" in call_args[1]["initial_prompt"]


# --- Server mode ---


def test_stt_client_server_mode():
    """STTClient in server mode creates an HTTP client."""
    client = STTClient(mode="server")
    assert client._mode == "server"
    assert client.available is True
    assert client._http is not None


async def test_transcribe_server():
    """Server transcription POSTs to the STT endpoint."""
    client = STTClient(mode="server")

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"text": "Hello from server"}
    mock_resp.raise_for_status = MagicMock()

    client._http.post = AsyncMock(return_value=mock_resp)
    wav_bytes = b"RIFF\x00\x00\x00\x00WAVEfmt fake wav data"
    result = await client.transcribe(wav_bytes, server_url="http://localhost:8001")

    assert result == "Hello from server"
    client._http.post.assert_called_once()

    call_args = client._http.post.call_args
    assert call_args[0][0] == "http://localhost:8001/transcribe"


# --- Invalid mode ---


def test_stt_client_invalid_mode():
    """STTClient raises ValueError for unknown mode."""
    with pytest.raises(ValueError, match="Unknown stt_mode"):
        STTClient(mode="banana")
