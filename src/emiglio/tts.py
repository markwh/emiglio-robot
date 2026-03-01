"""TTS client — inline (direct ElevenLabs API) or server (HTTP) mode."""

import io
import logging
import wave

import httpx

logger = logging.getLogger(__name__)


class TTSClient:
    """Synthesizes speech via ElevenLabs (inline) or HTTP (server mode)."""

    def __init__(
        self,
        mode: str = "inline",
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",
        model_id: str = "eleven_flash_v2_5",
    ) -> None:
        self._mode = mode
        self._voice_id = voice_id
        self._model_id = model_id
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

    async def synthesize(self, text: str, server_url: str = "") -> bytes | None:
        """Convert text to WAV audio bytes."""
        if self._mode == "inline":
            return await self._synthesize_inline(text)
        return await self._synthesize_server(text, server_url)

    async def _synthesize_inline(self, text: str) -> bytes | None:
        """Call ElevenLabs API directly and return WAV bytes."""
        if self._elevenlabs is None:
            return None

        try:
            raw_chunks = []
            async for chunk in self._elevenlabs.text_to_speech.convert(
                text=text,
                voice_id=self._voice_id,
                model_id=self._model_id,
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
