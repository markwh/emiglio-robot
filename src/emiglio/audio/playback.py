"""Audio playback to the robot's speaker via sounddevice."""

import asyncio
import io
import logging
import wave

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


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

        logger.info(
            "Playing audio: %.1fs @ %dHz",
            len(audio) / sample_rate / channels,
            sample_rate,
        )
        await asyncio.to_thread(sd.play, audio, samplerate=sample_rate)
        await asyncio.to_thread(sd.wait)
        logger.info("Playback complete")
