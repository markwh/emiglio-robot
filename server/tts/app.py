"""Text-to-speech service using Piper TTS."""

import io
import logging
import subprocess
import wave
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import Response
from pydantic import BaseModel

logger = logging.getLogger(__name__)

MODEL_DIR = Path("/app/models")
# Default voice — downloaded at build time
MODEL_NAME = "en_US-lessac-medium"
MODEL_PATH = MODEL_DIR / f"{MODEL_NAME}.onnx"
MODEL_CONFIG = MODEL_DIR / f"{MODEL_NAME}.onnx.json"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not MODEL_PATH.exists():
        logger.error("Piper model not found at %s", MODEL_PATH)
    else:
        logger.info("Piper model ready: %s", MODEL_NAME)
    yield


app = FastAPI(title="Emiglio TTS", lifespan=lifespan)


class SynthesizeRequest(BaseModel):
    text: str


@app.post("/synthesize")
async def synthesize(req: SynthesizeRequest):
    """Convert text to speech, return WAV audio bytes."""
    if not MODEL_PATH.exists():
        return Response(content="Model not found", status_code=503)

    # Run piper CLI and capture raw PCM output
    proc = subprocess.run(
        [
            "piper",
            "--model", str(MODEL_PATH),
            "--config", str(MODEL_CONFIG),
            "--output_raw",
        ],
        input=req.text.encode(),
        capture_output=True,
        timeout=30,
    )

    if proc.returncode != 0:
        logger.error("Piper failed: %s", proc.stderr.decode())
        return Response(content="TTS failed", status_code=500)

    # Wrap raw PCM (16-bit mono 22050Hz) in a WAV container
    raw_audio = proc.stdout
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
    return {"status": "ok", "model": MODEL_NAME, "model_exists": MODEL_PATH.exists()}
