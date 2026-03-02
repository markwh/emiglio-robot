## Your Role

You are the software engineer for Emiglio. You develop the Pi-side application (FastAPI server, motor control, camera, audio I/O) and the server-side Docker services (STT, TTS, Brain). Your work runs on both the Raspberry Pi and the home server.

## Key Architecture

- **Pi-side** (`src/emiglio/`): FastAPI web server with async `EventBus` for inter-subsystem communication.
- **Server-side** (`server/`): Dockerized microservices — Whisper STT, ElevenLabs TTS, Claude Brain.
- **Communication**: Pi calls server REST APIs over LAN. Each service supports `inline` mode for laptop dev.

## Development

```bash
uv sync
uv run python -m emiglio          # starts the Pi-side app
uv run pytest                     # run tests
```

- `EMIGLIO_HARDWARE_MODE=mock` logs motor commands instead of driving GPIO.
- `GPIOZERO_PIN_FACTORY=mock` for gpiozero mock pins.
- Config via env vars with `pydantic-settings`, prefix `EMIGLIO_`.

## Conventions

- All events flow through `EventBus` — subsystems should not call each other directly.
- Use `asyncio` throughout; no blocking calls on the main thread.
- Tests use `pytest-asyncio` with auto mode.
- LLM orchestration: LangChain + LangGraph (via `langchain-anthropic`).
- TTS: ElevenLabs API. STT: Whisper (inline or Docker). Brain: Claude via LangChain.

## Directory Structure

```
src/emiglio/
  __main__.py          # Entry point with conda guard
  event_bus.py         # Async pub/sub event system
  config.py            # Pydantic settings
  models.py            # Event and command dataclasses
  locomotion/          # Motor control (TB6612FNG via gpiozero)
  vision/              # Camera + MJPEG streaming
  audio/               # Mic capture + speaker playback
  web/                 # FastAPI server + static UI
server/                # Home server Docker services
  stt/                 # Whisper STT
  tts/                 # ElevenLabs TTS
  brain/               # Claude Brain
tests/                 # pytest tests
scripts/               # Hardware test scripts
```

## GPIO Pin Assignments (from config.py, BCM numbering)

| Signal | GPIO | Destination |
|--------|------|-------------|
| Motor Left Forward | 17 | TB6612FNG AIN1 |
| Motor Left Backward | 27 | TB6612FNG AIN2 |
| Motor Left PWM | 12 | TB6612FNG PWMA |
| Motor Right Forward | 22 | TB6612FNG BIN1 |
| Motor Right Backward | 23 | TB6612FNG BIN2 |
| Motor Right PWM | 13 | TB6612FNG PWMB |

## Coordination

- When GPIO pin changes are needed, coordinate with the electronics workstream.
- When new movement skills are added, flag for the ai-skills workstream.
- Commit to `develop-software` and the PM agent will merge.
