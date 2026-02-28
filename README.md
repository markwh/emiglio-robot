# Emiglio Robot

AI-powered vintage Emiglio toy robot (GP Toys, ~1980s-90s) rebuilt with modern internals: voice interaction, camera vision, and motor control — all driven by an LLM brain.

## Architecture

Split compute between a **Raspberry Pi 4B** (edge: motors, sensors, I/O) and a **Linux home server** (heavy compute: STT, TTS, LLM). Communication over local network REST APIs.

```
┌──────────────────────────────────┐     ┌─────────────────────────────┐
│  RASPBERRY PI 4B (edge)          │     │  HOME SERVER (compute)      │
│                                  │     │                             │
│  Locomotion (gpiozero)           │     │  STT (Whisper base)         │
│  Camera (OpenCV)                 │     │  TTS (Piper)                │
│  Audio (sounddevice)             │     │  Brain (Claude API)         │
│  Web UI (FastAPI + WebSocket)    │     │                             │
│  Conversation Manager            │     │  docker compose up          │
│                                  │     │                             │
│  All subsystems connected via    │     │                             │
│  async EventBus (pub/sub)        │     │                             │
└──────────────────────────────────┘     └─────────────────────────────┘
         Pi: real-time I/O                    Server: inference
         ~LAN, REST APIs~
```

## Quick Start

### Pi-side (or laptop dev)

```bash
uv sync
uv run python -m emiglio
# Open http://localhost:8080
```

In mock mode (default), motor commands are logged instead of driving GPIO. Set `EMIGLIO_HARDWARE_MODE=real` on the Pi with motors wired.

### Server-side

```bash
cd server
ANTHROPIC_API_KEY=sk-... docker compose up --build
```

Starts STT (port 8001), TTS (port 8002), and Brain (port 8003).

## Features

- **Joystick control** — drive the robot from your phone via a touch-friendly virtual joystick
- **Live camera feed** — MJPEG stream from USB webcam embedded in the dashboard
- **Voice interaction** — push-to-talk: speak → STT → LLM brain → TTS → robot speaks back
- **Text chat** — type messages to the robot when voice isn't convenient
- **Motor commands from AI** — the brain can issue movement commands ("move forward", "turn left") that drive the motors
- **Camera context** — ask "what do you see?" and the brain receives the current camera frame

## Configuration

All config via environment variables with `EMIGLIO_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `EMIGLIO_HARDWARE_MODE` | `mock` | `mock` for laptop dev, `real` for Pi GPIO |
| `EMIGLIO_WEB_PORT` | `8080` | Web UI port |
| `EMIGLIO_SERVER_STT_URL` | `http://localhost:8001` | STT service URL |
| `EMIGLIO_SERVER_TTS_URL` | `http://localhost:8002` | TTS service URL |
| `EMIGLIO_SERVER_BRAIN_URL` | `http://localhost:8003` | Brain service URL |
| `EMIGLIO_CAMERA_INDEX` | `0` | OpenCV camera device index |

## Hardware

### On Hand
- Raspberry Pi 4 Model B
- Linux PC/server (CPU-only)
- USB webcam, USB microphone
- Emiglio robot shell (body, base with motors, head with speaker)

### Shopping List
| Item | ~Cost | Purpose |
|------|-------|---------|
| TB6612FNG motor driver | $6 | Drive 2 DC motors from Pi GPIO |
| Jumper wires (M-F, M-M) | $6 | Pi GPIO to motor driver |
| Breadboard (half-size) | $4 | Prototyping |
| PAM8403 mini amp | $3 | Amplify Pi audio to speaker |
| 4xAA battery holder + batteries | $5 | Motor power supply |
| MicroSD card (32GB) | $10 | Pi OS |

## Project Structure

```
src/emiglio/              # Pi-side package
  __main__.py             # Entry point — wires all subsystems
  config.py               # Pydantic settings (env vars)
  event_bus.py            # Async pub/sub
  models.py               # Event/command dataclasses
  conversation.py         # Voice loop orchestrator
  locomotion/             # Motor control (gpiozero + TB6612FNG)
  vision/                 # Camera capture + MJPEG streaming
  audio/                  # Mic capture + speaker playback
  web/                    # FastAPI server + static UI

server/                   # Home server Docker services
  docker-compose.yml
  stt/                    # Whisper STT
  tts/                    # Piper TTS
  brain/                  # Claude API brain

scripts/                  # Hardware test scripts
tests/                    # pytest tests
```

## Development

```bash
uv sync                          # install deps
uv run python -m emiglio         # run (mock mode)
uv run pytest -v                 # run tests
```

All code runs on a laptop without Pi hardware — `gpiozero` MockFactory and `EMIGLIO_HARDWARE_MODE=mock` simulate GPIO. Camera uses the laptop webcam (same OpenCV API).

## Tests

```bash
uv run pytest -v
```

Tests cover: event bus, locomotion (joystick mixing, motor commands), vision (camera, MJPEG stream), brain command parsing, and conversation manager (command execution, graceful degradation).
