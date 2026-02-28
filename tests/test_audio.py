"""Tests for the audio subsystem."""

import io
import wave
import numpy as np
import pytest

try:
    from emiglio.audio.capture import AudioCapture, SAMPLE_RATE, CHANNELS
    from emiglio.audio.playback import AudioPlayback
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
