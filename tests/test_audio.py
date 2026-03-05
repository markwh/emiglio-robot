"""Tests for the audio subsystem."""

import io
import wave
import numpy as np
import pytest

try:
    from emiglio.audio.capture import AudioCapture, SAMPLE_RATE, CHANNELS
    from emiglio.audio.playback import AudioPlayback, _resample, STANDARD_RATES, FALLBACK_RATE
    _sounddevice_available = True
except OSError:
    _sounddevice_available = False

pytestmark = pytest.mark.skipif(
    not _sounddevice_available,
    reason="sounddevice/PortAudio not available on this system",
)


def _make_wav(duration: float = 0.1, sample_rate: int = 16000) -> bytes:
    """Create a short WAV file with a sine wave."""
    frames = int(duration * sample_rate)
    t = np.linspace(0, duration, frames, endpoint=False)
    audio = (np.sin(2 * np.pi * 440 * t) * 16000).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.tobytes())
    return buf.getvalue()


def test_capture_to_wav_format():
    """Verify _to_wav produces valid WAV."""
    capture = AudioCapture()
    audio = np.zeros(1600, dtype=np.int16)  # 0.1s of silence
    wav_bytes = capture._to_wav(audio)

    assert wav_bytes[:4] == b"RIFF"
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        assert wf.getnchannels() == CHANNELS
        assert wf.getframerate() == SAMPLE_RATE
        assert wf.getsampwidth() == 2


def test_wav_helper_produces_valid_wav():
    wav = _make_wav()
    assert wav[:4] == b"RIFF"
    buf = io.BytesIO(wav)
    with wave.open(buf, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getframerate() == 16000


def test_capture_constants():
    assert SAMPLE_RATE == 16000
    assert CHANNELS == 1


# --- Resampling tests ---


def test_resample_preserves_length_ratio():
    """Resampled audio length matches the expected ratio."""
    src = np.arange(1000, dtype=np.int16)
    result = _resample(src, 22050, 48000)
    expected_len = int(1000 * 48000 / 22050)
    assert len(result) == expected_len


def test_resample_noop_when_rates_match():
    """_resample returns the same array when src == dst rate."""
    src = np.arange(100, dtype=np.int16)
    result = _resample(src, 44100, 44100)
    assert result is src


def test_resample_preserves_dtype():
    """Output dtype matches input dtype for both int16 and int32."""
    for dtype in (np.int16, np.int32):
        src = np.arange(100, dtype=dtype)
        result = _resample(src, 22050, 48000)
        assert result.dtype == dtype


def test_resample_multichannel():
    """Resampling works on stereo (2-channel) audio."""
    frames = 500
    stereo = np.column_stack([
        np.arange(frames, dtype=np.int16),
        np.arange(frames, dtype=np.int16) * 2,
    ])
    result = _resample(stereo, 22050, 48000)
    expected_frames = int(frames * 48000 / 22050)
    assert result.shape == (expected_frames, 2)
    assert result.dtype == np.int16


@pytest.mark.parametrize("weird_rate", [24255, 17640, 33075, 12000])
def test_resample_various_nonstandard_rates(weird_rate):
    """Any non-standard rate resamples to the correct length."""
    n_samples = weird_rate  # 1 second of audio
    src = (np.sin(np.linspace(0, 2 * np.pi * 440, n_samples)) * 16000).astype(np.int16)
    result = _resample(src, weird_rate, FALLBACK_RATE)
    expected_len = int(n_samples * FALLBACK_RATE / weird_rate)
    assert len(result) == expected_len
    assert result.dtype == np.int16


async def test_play_wav_resamples_nonstandard_rate():
    """play_wav resamples non-standard sample rates before calling sd.play."""
    from unittest.mock import patch, MagicMock

    wav_bytes = _make_wav(duration=0.1, sample_rate=24255)
    playback = AudioPlayback()

    called_with = {}

    def mock_play(audio, samplerate=None):
        called_with["rate"] = samplerate
        called_with["len"] = len(audio)

    def mock_wait():
        pass

    with patch("emiglio.audio.playback.sd.play", mock_play), \
         patch("emiglio.audio.playback.sd.wait", mock_wait):
        await playback.play_wav(wav_bytes)

    assert called_with["rate"] == FALLBACK_RATE
    # Verify the audio was actually resampled (more samples at higher rate)
    original_samples = int(0.1 * 24255)
    expected_samples = int(original_samples * FALLBACK_RATE / 24255)
    assert called_with["len"] == expected_samples


async def test_play_wav_keeps_standard_rate():
    """play_wav does NOT resample when the rate is already standard."""
    from unittest.mock import patch

    wav_bytes = _make_wav(duration=0.1, sample_rate=22050)
    playback = AudioPlayback()

    called_with = {}

    def mock_play(audio, samplerate=None):
        called_with["rate"] = samplerate

    def mock_wait():
        pass

    with patch("emiglio.audio.playback.sd.play", mock_play), \
         patch("emiglio.audio.playback.sd.wait", mock_wait):
        await playback.play_wav(wav_bytes)

    assert called_with["rate"] == 22050
