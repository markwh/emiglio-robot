"""Text-to-speech service using ElevenLabs API."""

import io
import logging
import os
import wave
from contextlib import asynccontextmanager

from elevenlabs import AsyncElevenLabs
from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

client: AsyncElevenLabs | None = None
voice_id: str = ""
model_id: str = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    global client, voice_id, model_id
    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel
    model_id = os.environ.get("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")

    if api_key:
        client = AsyncElevenLabs(api_key=api_key)
        logger.info("ElevenLabs client initialized (voice=%s, model=%s)", voice_id, model_id)
    else:
        logger.warning("No ELEVENLABS_API_KEY set — TTS will return 503")
    yield
    client = None


app = FastAPI(title="Emiglio TTS", lifespan=lifespan)


class SynthesizeRequest(BaseModel):
    text: str


@app.post("/synthesize")
async def synthesize(req: SynthesizeRequest):
    """Convert text to speech, return WAV audio bytes."""
    if client is None:
        return Response(content="ElevenLabs API key not configured", status_code=503)

    # Get PCM audio from ElevenLabs (16-bit mono 22050Hz)
    raw_chunks = []
    async for chunk in client.text_to_speech.convert(
        text=req.text,
        voice_id=voice_id,
        model_id=model_id,
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

    logger.info("Synthesized %d chars -> %d bytes WAV", len(req.text), wav_buffer.tell())
    return Response(
        content=wav_buffer.getvalue(),
        media_type="audio/wav",
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "api_configured": client is not None,
        "voice_id": voice_id,
        "model_id": model_id,
    }
