"""STT client — ElevenLabs (default), inline Whisper, or server mode."""

import asyncio
import logging
import tempfile

import httpx

logger = logging.getLogger(__name__)


class STTClient:
    """Transcribes audio via ElevenLabs Scribe, local Whisper, or HTTP server."""

    # Domain vocabulary hint — helps Whisper spell robot-specific words correctly.
    INITIAL_PROMPT = "Emiglio, forward, backward, left, right, spin, wiggle, dance, stop."

    def __init__(
        self,
        mode: str = "elevenlabs",
        model: str = "small",
        language: str = "en",
        elevenlabs_api_key: str = "",
        elevenlabs_model: str = "scribe_v2",
    ) -> None:
        self._mode = mode
        self._model_name = model
        self._language = language
        self._whisper_model = None
        self._http = None
        self._elevenlabs_key = elevenlabs_api_key
        self._elevenlabs_model = elevenlabs_model

        if mode == "elevenlabs":
            if not elevenlabs_api_key:
                logger.warning("STT: elevenlabs mode but no API key provided")
            else:
                self._http = httpx.AsyncClient(timeout=30.0)
                logger.info("STT: ElevenLabs mode (model=%s)", elevenlabs_model)
        elif mode == "inline":
            try:
                import whisper

                self._whisper_model = whisper.load_model(model)
                logger.info("STT: inline mode (model=%s, language=%s)", model, language)
            except Exception as e:
                logger.warning("STT: failed to load Whisper model: %s", e)
        elif mode == "server":
            self._http = httpx.AsyncClient(timeout=30.0)
            logger.info("STT: server mode")
        else:
            raise ValueError(
                f"Unknown stt_mode: {mode!r} (expected 'elevenlabs', 'inline', or 'server')"
            )

    @property
    def available(self) -> bool:
        """True if the STT client is ready to handle requests."""
        if self._mode == "elevenlabs":
            return self._http is not None
        if self._mode == "inline":
            return self._whisper_model is not None
        return self._http is not None

    async def transcribe(self, wav_bytes: bytes, server_url: str = "") -> str:
        """Transcribe WAV audio bytes to text."""
        if self._mode == "elevenlabs":
            return await self._transcribe_elevenlabs(wav_bytes)
        if self._mode == "inline":
            return await self._transcribe_inline(wav_bytes)
        return await self._transcribe_server(wav_bytes, server_url)

    async def _transcribe_elevenlabs(self, wav_bytes: bytes) -> str:
        """Call ElevenLabs Scribe API."""
        if self._http is None:
            return ""

        try:
            resp = await self._http.post(
                "https://api.elevenlabs.io/v1/speech-to-text",
                headers={"xi-api-key": self._elevenlabs_key},
                files={"file": ("audio.wav", wav_bytes, "audio/wav")},
                data={"model_id": self._elevenlabs_model, "language_code": self._language},
            )
            resp.raise_for_status()
            return resp.json().get("text", "").strip()
        except Exception as e:
            logger.error("STT ElevenLabs request failed: %s", e)
            return ""

    async def _transcribe_inline(self, wav_bytes: bytes) -> str:
        """Run Whisper locally in a thread pool."""
        if self._whisper_model is None:
            return ""

        def _run():
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as f:
                f.write(wav_bytes)
                f.flush()
                result = self._whisper_model.transcribe(
                    f.name,
                    language=self._language,
                    initial_prompt=self.INITIAL_PROMPT,
                )
            return result.get("text", "").strip()

        try:
            return await asyncio.to_thread(_run)
        except Exception as e:
            logger.error("STT inline transcription failed: %s", e)
            return ""

    async def _transcribe_server(self, wav_bytes: bytes, server_url: str) -> str:
        """POST to the STT HTTP server."""
        if self._http is None:
            return ""

        try:
            resp = await self._http.post(
                f"{server_url}/transcribe",
                files={"audio": ("audio.wav", wav_bytes, "audio/wav")},
            )
            resp.raise_for_status()
            return resp.json().get("text", "").strip()
        except Exception as e:
            logger.error("STT server request failed: %s", e)
            return ""

    async def close(self) -> None:
        """Clean up resources."""
        if self._http:
            await self._http.aclose()
