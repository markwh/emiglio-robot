# Emiglio Robot

AI-powered vintage Emiglio toy robot. Split architecture: Raspberry Pi 4B (edge I/O) + Linux home server (inference).

## Dev Setup

```bash
uv sync
uv run python -m emiglio          # starts the Pi-side app
uv run pytest                     # run tests
```

## Architecture

- **Pi-side** (`src/emiglio/`): FastAPI web server, motor control, camera, audio I/O. All subsystems communicate via async `EventBus`.
- **Server-side** (`server/`): Dockerized STT (Whisper), TTS (Piper), Brain (Claude API) services.
- **Communication**: Pi calls server REST APIs over LAN.

## Key Conventions

- Config via env vars with `pydantic-settings`. Prefix: `EMIGLIO_`.
- `EMIGLIO_HARDWARE_MODE=mock` logs motor commands instead of driving GPIO (for laptop dev).
- `GPIOZERO_PIN_FACTORY=mock` for gpiozero mock pins.
- All events flow through `EventBus` -- subsystems should not call each other directly.
- Use `asyncio` throughout; no blocking calls on the main thread.
- Tests use `pytest-asyncio` with auto mode.

## Project Layout

```
src/emiglio/           # Pi-side package (installed as 'emiglio')
  event_bus.py         # Async pub/sub event system
  config.py            # Pydantic settings
  models.py            # Event and command dataclasses
  locomotion/          # Motor control
  vision/              # Camera + MJPEG streaming
  audio/               # Mic capture + speaker playback
  web/                 # FastAPI server + static UI
server/                # Home server Docker services
scripts/               # Hardware test scripts
tests/                 # pytest tests
```
