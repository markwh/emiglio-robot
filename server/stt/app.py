"""Speech-to-text service using OpenAI Whisper."""

import io
import logging
import tempfile
from contextlib import asynccontextmanager

import whisper
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    logger.info("Loading Whisper model (base)...")
    model = whisper.load_model("base")
    logger.info("Whisper model loaded")
    yield
    model = None


app = FastAPI(title="Emiglio STT", lifespan=lifespan)


@app.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Accept a WAV file and return the transcript."""
    audio_bytes = await audio.read()

    # Whisper needs a file path, so write to a temp file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        result = model.transcribe(tmp.name, language="en")

    text = result["text"].strip()
    logger.info("Transcribed: %s", text)
    return {"text": text}


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}
