"""Audio playback to the robot's speaker via sounddevice."""

import asyncio
import io
import logging
import wave

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


FALLBACK_RATE = 48000


def _device_supports_rate(rate: int) -> bool:
    """Check whether the default output device supports a given sample rate."""
    try:
        sd.check_output_settings(samplerate=rate)
        return True
    except sd.PortAudioError:
        return False


def _resample(audio: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    """Resample audio using linear interpolation."""
    if src_rate == dst_rate:
        return audio
    ratio = dst_rate / src_rate
    src_len = len(audio)
    dst_len = int(src_len * ratio)
    src_x = np.arange(src_len)
    dst_x = np.linspace(0, src_len - 1, dst_len)
    if audio.ndim == 1:
        return np.interp(dst_x, src_x, audio).astype(audio.dtype)
    # Multi-channel: resample each channel
    return np.column_stack(
        [np.interp(dst_x, src_x, audio[:, c]).astype(audio.dtype) for c in range(audio.shape[1])]
    )


class AudioPlayback:
    """Plays WAV audio through the system's default output device."""

    async def play_wav(self, wav_bytes: bytes) -> None:
        """Play WAV audio bytes through the speaker."""
        buf = io.BytesIO(wav_bytes)
        with wave.open(buf, "rb") as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            raw = wf.readframes(wf.getnframes())

        if sample_width == 2:
            dtype = np.int16
        elif sample_width == 4:
            dtype = np.int32
        else:
            logger.error("Unsupported sample width: %d", sample_width)
            return

        audio = np.frombuffer(raw, dtype=dtype)
        if channels > 1:
            audio = audio.reshape(-1, channels)

        # Resample if the device doesn't support this rate
        if not _device_supports_rate(sample_rate):
            target_rate = FALLBACK_RATE
            logger.info(
                "Resampling from %dHz to %dHz (unsupported by device)",
                sample_rate, target_rate,
            )
            audio = _resample(audio, sample_rate, target_rate)
            sample_rate = target_rate

        logger.info(
            "Playing audio: %.1fs @ %dHz",
            len(audio) / sample_rate / (channels if audio.ndim == 1 else 1),
            sample_rate,
        )
        await asyncio.to_thread(sd.play, audio, samplerate=sample_rate)
        await asyncio.to_thread(sd.wait)
        logger.info("Playback complete")
