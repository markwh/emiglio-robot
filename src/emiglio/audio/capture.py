"""Microphone audio capture using sounddevice."""

import asyncio
import io
import logging
import wave

import numpy as np
import sounddevice as sd

from emiglio.audio.playback import _resample
from emiglio.config import settings

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000  # 16kHz for Whisper
CHANNELS = 1
DTYPE = "int16"


def _pick_capture_rate(desired: int) -> int:
    """Return *desired* if the input device supports it, else a fallback."""
    try:
        sd.check_input_settings(samplerate=desired)
        return desired
    except sd.PortAudioError:
        pass
    for rate in (48000, 44100):
        try:
            sd.check_input_settings(samplerate=rate)
            logger.info("Input device doesn't support %dHz, using %dHz", desired, rate)
            return rate
        except sd.PortAudioError:
            continue
    return desired  # let it fail loudly if nothing works


class AudioCapture:
    """Records audio from the USB microphone.

    Uses a simple voice-activity detection approach: record for a fixed
    duration when triggered, or record until silence is detected.
    """

    def __init__(self) -> None:
        self._sample_rate = SAMPLE_RATE
        self._capture_rate: int | None = None

    @property
    def capture_rate(self) -> int:
        if self._capture_rate is None:
            self._capture_rate = _pick_capture_rate(self._sample_rate)
        return self._capture_rate

    async def record_seconds(self, duration: float = 5.0) -> bytes:
        """Record for a fixed duration, return WAV bytes."""
        logger.info("Recording %.1fs of audio...", duration)
        rate = self.capture_rate
        frames = int(duration * rate)

        audio = await asyncio.to_thread(
            sd.rec, frames, samplerate=rate, channels=CHANNELS, dtype=DTYPE
        )
        await asyncio.to_thread(sd.wait)

        audio = self._to_target_rate(audio, rate)
        logger.info("Recording complete (%d samples)", len(audio))
        return self._to_wav(audio)

    async def record_until_silence(
        self,
        max_duration: float = 10.0,
        silence_threshold: float = 500.0,
        silence_duration: float = 1.5,
        chunk_duration: float = 0.1,
        calibration_chunks: int = 5,
        calibration_multiplier: float = 3.0,
    ) -> bytes:
        """Record until silence is detected or max duration is reached.

        Args:
            max_duration: Maximum recording length in seconds.
            silence_threshold: RMS amplitude below which is "silence".
                If the noise floor (measured during the first few chunks)
                is close to or above this value, the threshold is raised
                automatically.
            silence_duration: How long silence must last to stop (seconds).
            chunk_duration: Size of each recording chunk (seconds).
            calibration_chunks: Number of initial chunks used to measure
                the ambient noise floor.
            calibration_multiplier: The speech threshold is set to
                ``max(silence_threshold, noise_floor * multiplier)``.
        """
        logger.info("Recording (silence-detect, max %.1fs)...", max_duration)
        rate = self.capture_rate
        chunk_frames = int(chunk_duration * rate)
        max_chunks = int(max_duration / chunk_duration)
        silence_chunks_needed = int(silence_duration / chunk_duration)

        chunks: list[np.ndarray] = []
        silent_count = 0
        has_speech = False
        rms_values: list[float] = []
        effective_threshold = silence_threshold

        for i in range(max_chunks):
            chunk = await asyncio.to_thread(
                sd.rec, chunk_frames,
                samplerate=rate, channels=CHANNELS, dtype=DTYPE,
            )
            await asyncio.to_thread(sd.wait)
            chunks.append(chunk)

            rms = float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
            rms_values.append(rms)

            # After calibration period, adapt threshold to noise floor
            if i == calibration_chunks - 1:
                noise_floor = np.mean(rms_values)
                effective_threshold = max(silence_threshold, noise_floor * calibration_multiplier)
                logger.info(
                    "Noise floor: %.1f RMS, effective speech threshold: %.1f",
                    noise_floor, effective_threshold,
                )

            if rms > effective_threshold:
                has_speech = True
                silent_count = 0
            else:
                silent_count += 1

            # Log RMS periodically for diagnostics
            if i % 10 == 0:
                logger.debug("Capture chunk %d: RMS=%.1f (threshold=%.1f)", i, rms, effective_threshold)

            # Stop if we've had speech followed by enough silence
            if has_speech and silent_count >= silence_chunks_needed:
                logger.info("Silence detected, stopping recording")
                break

        if rms_values:
            peak_rms = max(rms_values)
            avg_rms = np.mean(rms_values)
            logger.info(
                "Capture stats: %d chunks, avg RMS=%.1f, peak RMS=%.1f, threshold=%.1f, speech_detected=%s",
                len(rms_values), avg_rms, peak_rms, effective_threshold, has_speech,
            )

        audio = self._to_target_rate(np.concatenate(chunks), rate)
        logger.info("Recorded %d samples (%.1fs)", len(audio), len(audio) / self._sample_rate)
        return self._to_wav(audio)

    def _to_target_rate(self, audio: np.ndarray, recorded_rate: int) -> np.ndarray:
        """Resample captured audio to the target sample rate if needed."""
        if recorded_rate == self._sample_rate:
            return audio
        return _resample(audio, recorded_rate, self._sample_rate)

    def _to_wav(self, audio: np.ndarray) -> bytes:
        """Convert numpy audio array to WAV bytes."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self._sample_rate)
            wf.writeframes(audio.tobytes())
        return buf.getvalue()
