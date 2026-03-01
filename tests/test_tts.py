"""Tests for the TTS client (inline ElevenLabs and server modes)."""

import sys
import wave
import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from emiglio.tts import TTSClient


def _make_mock_elevenlabs():
    """Create a mock elevenlabs module and AsyncElevenLabs class."""
    mock_client_instance = MagicMock()
    mock_async_class = MagicMock(return_value=mock_client_instance)
    mock_module = MagicMock()
    mock_module.AsyncElevenLabs = mock_async_class
    return mock_module, mock_client_instance


def test_tts_client_inline_mode():
    """TTSClient in inline mode creates an ElevenLabs client."""
    mock_module, mock_client = _make_mock_elevenlabs()
    with patch.dict(sys.modules, {"elevenlabs": mock_module}):
        client = TTSClient(mode="inline", voice_id="test-voice", model_id="test-model")
    assert client._mode == "inline"
    assert client.available is True
    assert client._elevenlabs is mock_client


def test_tts_client_server_mode():
    """TTSClient in server mode creates an HTTP client."""
    client = TTSClient(mode="server")
    assert client._mode == "server"
    assert client.available is True
    assert client._http is not None


def test_tts_client_invalid_mode():
    """TTSClient raises ValueError for unknown mode."""
    with pytest.raises(ValueError, match="Unknown tts_mode"):
        TTSClient(mode="banana")


async def test_synthesize_inline():
    """Inline synthesis calls ElevenLabs and returns valid WAV bytes."""
    # Simulate PCM audio chunks from ElevenLabs
    pcm_chunk_1 = b"\x00\x01" * 100
    pcm_chunk_2 = b"\x02\x03" * 100

    async def fake_convert(**kwargs):
        yield pcm_chunk_1
        yield pcm_chunk_2

    mock_module, mock_client = _make_mock_elevenlabs()
    mock_client.text_to_speech.convert = fake_convert

    with patch.dict(sys.modules, {"elevenlabs": mock_module}):
        client = TTSClient(mode="inline", voice_id="v1", model_id="m1")

    result = await client.synthesize("Hello world")
    assert result is not None

    # Verify it's valid WAV
    buf = io.BytesIO(result)
    with wave.open(buf, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 22050
        frames = wf.readframes(wf.getnframes())
        assert frames == pcm_chunk_1 + pcm_chunk_2


async def test_synthesize_server():
    """Server synthesis POSTs to the TTS endpoint."""
    client = TTSClient(mode="server")

    fake_wav = b"RIFF\x00\x00\x00\x00WAVEfmt fake wav"
    mock_resp = MagicMock()
    mock_resp.content = fake_wav
    mock_resp.raise_for_status = MagicMock()

    client._http.post = AsyncMock(return_value=mock_resp)
    result = await client.synthesize("Hello", server_url="http://localhost:8002")

    assert result == fake_wav
    client._http.post.assert_called_once()

    call_args = client._http.post.call_args
    assert call_args[0][0] == "http://localhost:8002/synthesize"
    payload = call_args[1]["json"]
    assert payload == {"text": "Hello"}
