"""Tests for the STT client (inline Whisper and server modes)."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from emiglio.stt import STTClient


def _make_mock_whisper(mock_model=None):
    """Create a mock whisper module and inject into sys.modules."""
    mock_whisper = MagicMock()
    mock_whisper.load_model.return_value = mock_model or MagicMock()
    return mock_whisper


def test_stt_client_inline_mode():
    """STTClient in inline mode loads a Whisper model (or warns if unavailable)."""
    mock_whisper = _make_mock_whisper()
    with patch.dict(sys.modules, {"whisper": mock_whisper}):
        client = STTClient(mode="inline", model="base")
    assert client._mode == "inline"
    assert client.available is True
    mock_whisper.load_model.assert_called_once_with("base")


def test_stt_client_server_mode():
    """STTClient in server mode creates an HTTP client."""
    client = STTClient(mode="server")
    assert client._mode == "server"
    assert client.available is True
    assert client._http is not None


def test_stt_client_invalid_mode():
    """STTClient raises ValueError for unknown mode."""
    with pytest.raises(ValueError, match="Unknown stt_mode"):
        STTClient(mode="banana")


async def test_transcribe_inline():
    """Inline transcription writes WAV to tempfile and calls whisper.transcribe."""
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": " Hello, world! "}

    mock_whisper = _make_mock_whisper(mock_model)
    with patch.dict(sys.modules, {"whisper": mock_whisper}):
        client = STTClient(mode="inline", model="base")

    wav_bytes = b"RIFF\x00\x00\x00\x00WAVEfmt fake wav data"
    result = await client.transcribe(wav_bytes)

    assert result == "Hello, world!"
    mock_model.transcribe.assert_called_once()
    # Verify the tempfile path was passed
    call_args = mock_model.transcribe.call_args[0]
    assert call_args[0].endswith(".wav")


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
