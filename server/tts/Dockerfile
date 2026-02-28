FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        piper \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic

# Download default voice model
RUN mkdir -p /app/models && \
    pip install --no-cache-dir piper-tts && \
    python -c " \
from piper.download import ensure_voice_exists; \
ensure_voice_exists('en_US-lessac-medium', ['/app/models'], '/app/models', None) \
" || echo 'Model download will happen at runtime if needed'

COPY app.py .

EXPOSE 8002

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8002"]
