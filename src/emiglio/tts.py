"""TTS client — inline (direct ElevenLabs API) or server (HTTP) mode."""

import io
import logging
import wave
from pathlib import Path

import httpx
import numpy as np

logger = logging.getLogger(__name__)

VOICE_SAVE_PATH = Path.home() / ".config" / "emiglio" / "tts_voice_id"


def robotize_wav(
    wav_bytes: bytes,
    downsample: int = 3,
    bit_depth: int = 5,
    pitch_shift: float = 1.1,
) -> bytes:
    """Apply lo-fi robot effect: downsample + bit crush + pitch shift.

    pitch_shift > 1.0 raises pitch (and speeds up proportionally).
    """
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        sr = wf.getframerate()
        ch = wf.getnchannels()
        sw = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())

    audio = np.frombuffer(raw, dtype=np.int16).copy()

    # Downsample: decimate then repeat (creates stepped aliasing)
    decimated = audio[::downsample]
    audio = np.repeat(decimated, downsample)[: len(audio)]

    # Bit crush: reduce effective bit depth
    shift = 16 - bit_depth
    if shift > 0:
        audio = (audio >> shift) << shift

    # Pitch shift: write a higher sample rate so playback is faster/higher
    out_sr = int(sr * pitch_shift) if pitch_shift != 1.0 else sr

    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setnchannels(ch)
        wf.setsampwidth(sw)
        wf.setframerate(out_sr)
        wf.writeframes(audio.tobytes())
    return out.getvalue()


class TTSClient:
    """Synthesizes speech via ElevenLabs (inline) or HTTP (server mode)."""

    def __init__(
        self,
        mode: str = "inline",
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        model_id: str = "eleven_flash_v2_5",
        robot_effect: bool = True,
    ) -> None:
        self._mode = mode
        self._voice_id = self._load_voice_id() or voice_id
        self._model_id = model_id
        self._robot_effect = robot_effect
        self._elevenlabs = None
        self._http = None

        if mode == "inline":
            try:
                from elevenlabs import AsyncElevenLabs

                self._elevenlabs = AsyncElevenLabs()
                logger.info("TTS: inline mode (voice=%s, model=%s)", voice_id, model_id)
            except Exception as e:
                logger.warning("TTS: failed to create ElevenLabs client: %s", e)
        elif mode == "server":
            self._http = httpx.AsyncClient(timeout=30.0)
            logger.info("TTS: server mode")
        else:
            raise ValueError(f"Unknown tts_mode: {mode!r} (expected 'inline' or 'server')")

    @property
    def available(self) -> bool:
        """True if the TTS client is ready to handle requests."""
        if self._mode == "inline":
            return self._elevenlabs is not None
        return self._http is not None

    @property
    def voice_id(self) -> str:
        return self._voice_id

    @property
    def model_id(self) -> str:
        return self._model_id

    def set_voice(self, voice_id: str) -> None:
        """Change the active voice for all future synthesis calls and persist to disk."""
        self._voice_id = voice_id
        self._save_voice_id(voice_id)
        logger.info("TTS: voice changed to %s (saved)", voice_id)

    @staticmethod
    def _save_voice_id(voice_id: str) -> None:
        try:
            VOICE_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
            VOICE_SAVE_PATH.write_text(voice_id.strip())
        except Exception as e:
            logger.warning("TTS: failed to save voice_id: %s", e)

    @staticmethod
    def _load_voice_id() -> str | None:
        try:
            if VOICE_SAVE_PATH.exists():
                saved = VOICE_SAVE_PATH.read_text().strip()
                if saved:
                    logger.info("TTS: loaded saved voice_id=%s", saved)
                    return saved
        except Exception as e:
            logger.warning("TTS: failed to load saved voice_id: %s", e)
        return None

    async def list_voices(self) -> list[dict]:
        """Return simplified voice info from ElevenLabs API."""
        if self._elevenlabs is None:
            return []
        try:
            response = await self._elevenlabs.voices.get_all()
            voices = []
            for v in response.voices:
                voices.append({
                    "voice_id": v.voice_id,
                    "name": v.name,
                    "category": getattr(v, "category", None),
                    "labels": dict(v.labels) if v.labels else {},
                    "description": getattr(v, "description", None) or "",
                    "preview_url": getattr(v, "preview_url", None) or "",
                })
            return voices
        except Exception as e:
            logger.error("TTS list_voices failed: %s", e)
            return []

    async def synthesize(
        self,
        text: str,
        server_url: str = "",
        voice_id: str | None = None,
        model_id: str | None = None,
    ) -> bytes | None:
        """Convert text to WAV audio bytes. Optional overrides for voice/model."""
        if self._mode == "inline":
            wav = await self._synthesize_inline(
                text,
                voice_id=voice_id or self._voice_id,
                model_id=model_id or self._model_id,
            )
        else:
            wav = await self._synthesize_server(text, server_url)

        if wav is not None and self._robot_effect:
            wav = robotize_wav(wav)
        return wav

    async def _synthesize_inline(
        self, text: str, voice_id: str | None = None, model_id: str | None = None
    ) -> bytes | None:
        """Call ElevenLabs API directly and return WAV bytes."""
        if self._elevenlabs is None:
            return None

        try:
            raw_chunks = []
            async for chunk in self._elevenlabs.text_to_speech.convert(
                text=text,
                voice_id=voice_id or self._voice_id,
                model_id=model_id or self._model_id,
                output_format="pcm_22050",
            ):
                raw_chunks.append(chunk)

            raw_audio = b"".join(raw_chunks)

            # Wrap raw PCM (16-bit mono 22050Hz) in a WAV container
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(22050)
                wf.writeframes(raw_audio)

            logger.info("TTS synthesized %d chars -> %d bytes WAV", len(text), wav_buffer.tell())
            return wav_buffer.getvalue()
        except Exception as e:
            logger.error("TTS inline synthesis failed: %s", e)
            return None

    async def _synthesize_server(self, text: str, server_url: str) -> bytes | None:
        """POST to the TTS HTTP server."""
        if self._http is None:
            return None

        try:
            resp = await self._http.post(
                f"{server_url}/synthesize",
                json={"text": text},
            )
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            logger.error("TTS server request failed: %s", e)
            return None

    async def close(self) -> None:
        """Clean up resources."""
        if self._http:
            await self._http.aclose()
