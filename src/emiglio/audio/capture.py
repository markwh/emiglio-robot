"""Microphone audio capture using sounddevice."""

import asyncio
import io
import logging
import wave

import numpy as np
import sounddevice as sd

from emiglio.config import settings

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000  # 16kHz for Whisper
CHANNELS = 1
DTYPE = "int16"


class AudioCapture:
    """Records audio from the USB microphone.

    Uses a simple voice-activity detection approach: record for a fixed
    duration when triggered, or record until silence is detected.
    """

    def __init__(self) -> None:
        self._sample_rate = SAMPLE_RATE

    async def record_seconds(self, duration: float = 5.0) -> bytes:
        """Record for a fixed duration, return WAV bytes."""
        logger.info("Recording %.1fs of audio...", duration)
        frames = int(duration * self._sample_rate)

        audio = await asyncio.to_thread(
            sd.rec, frames, samplerate=self._sample_rate, channels=CHANNELS, dtype=DTYPE
        )
        await asyncio.to_thread(sd.wait)

        logger.info("Recording complete (%d samples)", len(audio))
        return self._to_wav(audio)

    async def record_until_silence(
        self,
        max_duration: float = 10.0,
        silence_threshold: float = 500.0,
        silence_duration: float = 1.5,
        chunk_duration: float = 0.1,
    ) -> bytes:
        """Record until silence is detected or max duration is reached.

        Args:
            max_duration: Maximum recording length in seconds.
            silence_threshold: RMS amplitude below which is "silence".
            silence_duration: How long silence must last to stop (seconds).
            chunk_duration: Size of each recording chunk (seconds).
        """
        logger.info("Recording (silence-detect, max %.1fs)...", max_duration)
        chunk_frames = int(chunk_duration * self._sample_rate)
        max_chunks = int(max_duration / chunk_duration)
        silence_chunks_needed = int(silence_duration / chunk_duration)

        chunks: list[np.ndarray] = []
        silent_count = 0
        has_speech = False

        for _ in range(max_chunks):
            chunk = await asyncio.to_thread(
                sd.rec, chunk_frames,
                samplerate=self._sample_rate, channels=CHANNELS, dtype=DTYPE,
            )
            await asyncio.to_thread(sd.wait)
            chunks.append(chunk)

            rms = np.sqrt(np.mean(chunk.astype(np.float32) ** 2))
            if rms > silence_threshold:
                has_speech = True
                silent_count = 0
            else:
                silent_count += 1

            # Stop if we've had speech followed by enough silence
            if has_speech and silent_count >= silence_chunks_needed:
                logger.info("Silence detected, stopping recording")
                break

        audio = np.concatenate(chunks)
        logger.info("Recorded %d samples (%.1fs)", len(audio), len(audio) / self._sample_rate)
        return self._to_wav(audio)

    def _to_wav(self, audio: np.ndarray) -> bytes:
        """Convert numpy audio array to WAV bytes."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self._sample_rate)
            wf.writeframes(audio.tobytes())
        return buf.getvalue()
