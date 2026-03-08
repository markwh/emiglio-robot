"""Tests for the TTS client (ElevenLabs)."""

import sys
import wave
import io
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from emiglio.tts import TTSClient, robotize_wav


def _make_mock_elevenlabs():
    """Create a mock elevenlabs module and AsyncElevenLabs class."""
    mock_client_instance = MagicMock()
    mock_async_class = MagicMock(return_value=mock_client_instance)
    mock_module = MagicMock()
    mock_module.AsyncElevenLabs = mock_async_class
    return mock_module, mock_client_instance


def test_tts_client_creates_elevenlabs():
    """TTSClient creates an ElevenLabs client."""
    mock_module, mock_client = _make_mock_elevenlabs()
    with patch.dict(sys.modules, {"elevenlabs": mock_module}):
        client = TTSClient(voice_id="test-voice", model_id="test-model")
    assert client.available is True
    assert client._elevenlabs is mock_client


async def test_synthesize():
    """Synthesis calls ElevenLabs and returns valid WAV bytes."""
    # Simulate PCM audio chunks from ElevenLabs
    pcm_chunk_1 = b"\x00\x01" * 100
    pcm_chunk_2 = b"\x02\x03" * 100

    async def fake_convert(**kwargs):
        yield pcm_chunk_1
        yield pcm_chunk_2

    mock_module, mock_client = _make_mock_elevenlabs()
    mock_client.text_to_speech.convert = fake_convert

    with patch.dict(sys.modules, {"elevenlabs": mock_module}):
        client = TTSClient(voice_id="v1", model_id="m1", robot_effect=False)

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
        client = TTSClient(voice_id="v1", model_id="m1")

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
        client = TTSClient(voice_id="default-voice", model_id="default-model")

    await client.synthesize("Hi", voice_id="override-voice", model_id="override-model")
    assert call_kwargs["voice_id"] == "override-voice"
    assert call_kwargs["model_id"] == "override-model"


def test_set_voice():
    """set_voice() updates the voice_id property."""
    mock_module, mock_client = _make_mock_elevenlabs()
    with (
        patch.dict(sys.modules, {"elevenlabs": mock_module}),
        patch("emiglio.tts.TTSClient._load_voice_id", return_value=None),
        patch("emiglio.tts.TTSClient._save_voice_id"),
    ):
        client = TTSClient(voice_id="original", model_id="m1")

    assert client.voice_id == "original"
    with patch("emiglio.tts.TTSClient._save_voice_id"):
        client.set_voice("new-voice")
    assert client.voice_id == "new-voice"


def _make_wav(samples: np.ndarray, sr: int = 22050) -> bytes:
    """Helper: wrap int16 numpy array in WAV bytes."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


def test_robotize_wav_returns_valid_wav():
    """robotize_wav() returns valid WAV with same format."""
    samples = np.sin(np.linspace(0, 2 * np.pi * 440, 22050)) * 16000
    samples = samples.astype(np.int16)
    wav_in = _make_wav(samples)

    wav_out = robotize_wav(wav_in, pitch_shift=1.0)
    buf = io.BytesIO(wav_out)
    with wave.open(buf, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 22050
        assert wf.getnframes() == len(samples)


def test_robotize_wav_modifies_audio():
    """robotize_wav() actually changes the audio data."""
    samples = np.sin(np.linspace(0, 2 * np.pi * 440, 22050)) * 16000
    samples = samples.astype(np.int16)
    wav_in = _make_wav(samples)

    wav_out = robotize_wav(wav_in)

    buf = io.BytesIO(wav_out)
    with wave.open(buf, "rb") as wf:
        out_samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
    assert not np.array_equal(samples, out_samples)


def test_robotize_wav_bit_crush():
    """Bit crush zeroes the low bits of samples."""
    samples = np.array([0x7FFF, 0x1234, -0x5678], dtype=np.int16)
    wav_in = _make_wav(samples)

    wav_out = robotize_wav(wav_in, downsample=1, bit_depth=8)

    buf = io.BytesIO(wav_out)
    with wave.open(buf, "rb") as wf:
        out = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
    # With bit_depth=8, shift=8, low 8 bits should be zero
    for s in out:
        assert int(s) & 0xFF == 0


def test_robotize_wav_pitch_shift():
    """pitch_shift > 1.0 raises the output sample rate."""
    samples = np.sin(np.linspace(0, 2 * np.pi * 440, 22050)) * 16000
    samples = samples.astype(np.int16)
    wav_in = _make_wav(samples, sr=22050)

    wav_out = robotize_wav(wav_in, downsample=1, bit_depth=16, pitch_shift=1.1)
    buf = io.BytesIO(wav_out)
    with wave.open(buf, "rb") as wf:
        assert wf.getframerate() == int(22050 * 1.1)
        assert wf.getnframes() == len(samples)


async def test_synthesize_applies_robot_effect():
    """synthesize() applies robot effect when enabled."""
    # Use varied sample data so the effect is observable
    samples = np.sin(np.linspace(0, 2 * np.pi * 440, 600)) * 16000
    pcm = samples.astype(np.int16).tobytes()

    async def fake_convert(**kwargs):
        yield pcm

    mock_module, mock_client = _make_mock_elevenlabs()
    mock_client.text_to_speech.convert = fake_convert

    with patch.dict(sys.modules, {"elevenlabs": mock_module}):
        client = TTSClient(voice_id="v1", model_id="m1", robot_effect=True)

    result = await client.synthesize("Hello")
    assert result is not None

    # The raw PCM without effect
    raw_wav = io.BytesIO()
    with wave.open(raw_wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(pcm)
    no_effect = raw_wav.getvalue()

    assert result != no_effect


async def test_synthesize_skips_robot_effect_when_disabled():
    """synthesize() returns unmodified WAV when robot_effect=False."""
    pcm = b"\x00\x10" * 200

    async def fake_convert(**kwargs):
        yield pcm

    mock_module, mock_client = _make_mock_elevenlabs()
    mock_client.text_to_speech.convert = fake_convert

    with patch.dict(sys.modules, {"elevenlabs": mock_module}):
        client = TTSClient(voice_id="v1", model_id="m1", robot_effect=False)

    result = await client.synthesize("Hello")
    assert result is not None

    # Should match unprocessed WAV
    raw_wav = io.BytesIO()
    with wave.open(raw_wav, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(22050)
        wf.writeframes(pcm)
    expected = raw_wav.getvalue()

    assert result == expected
