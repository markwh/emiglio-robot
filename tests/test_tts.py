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


async def test_list_voices():
    """list_voices() returns simplified dicts from ElevenLabs API."""
    mock_module, mock_client = _make_mock_elevenlabs()

    voice1 = MagicMock()
    voice1.voice_id = "v1"
    voice1.name = "Rachel"
    voice1.category = "premade"
    voice1.labels = {"accent": "american", "age": "young"}
    voice1.description = "A calm voice"
    voice1.preview_url = "https://example.com/preview1.mp3"

    voice2 = MagicMock()
    voice2.voice_id = "v2"
    voice2.name = "Dave"
    voice2.category = "cloned"
    voice2.labels = None
    voice2.description = None
    voice2.preview_url = None

    response = MagicMock()
    response.voices = [voice1, voice2]
    mock_client.voices.get_all = AsyncMock(return_value=response)

    with patch.dict(sys.modules, {"elevenlabs": mock_module}):
        client = TTSClient(mode="inline", voice_id="v1", model_id="m1")

    result = await client.list_voices()
    assert len(result) == 2
    assert result[0]["voice_id"] == "v1"
    assert result[0]["name"] == "Rachel"
    assert result[0]["category"] == "premade"
    assert result[0]["labels"] == {"accent": "american", "age": "young"}
    assert result[0]["description"] == "A calm voice"
    assert result[0]["preview_url"] == "https://example.com/preview1.mp3"
    assert result[1]["voice_id"] == "v2"
    assert result[1]["labels"] == {}
    assert result[1]["description"] == ""


async def test_synthesize_with_voice_override():
    """synthesize() passes override voice_id/model_id to the ElevenLabs API."""
    call_kwargs = {}

    async def fake_convert(**kwargs):
        call_kwargs.update(kwargs)
        yield b"\x00\x01" * 50

    mock_module, mock_client = _make_mock_elevenlabs()
    mock_client.text_to_speech.convert = fake_convert

    with patch.dict(sys.modules, {"elevenlabs": mock_module}):
        client = TTSClient(mode="inline", voice_id="default-voice", model_id="default-model")

    await client.synthesize("Hi", voice_id="override-voice", model_id="override-model")
    assert call_kwargs["voice_id"] == "override-voice"
    assert call_kwargs["model_id"] == "override-model"


def test_set_voice():
    """set_voice() updates the voice_id property."""
    mock_module, mock_client = _make_mock_elevenlabs()
    with patch.dict(sys.modules, {"elevenlabs": mock_module}):
        client = TTSClient(mode="inline", voice_id="original", model_id="m1")

    assert client.voice_id == "original"
    client.set_voice("new-voice")
    assert client.voice_id == "new-voice"
