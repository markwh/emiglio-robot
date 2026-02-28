# Workstream: Software

**Branch:** `develop-software`
**Scope:** All Pi-side and server-side code for the Emiglio robot.

## Your Role

You are the software development agent for Emiglio. You own all code in `src/emiglio/`, `server/`, `tests/`, and `scripts/`. Your job is to implement features, fix bugs, improve test coverage, and keep the software ready for integration with hardware.

## What's In Scope

- **Pi-side application** (`src/emiglio/`): FastAPI web server, event bus, locomotion, vision, audio, conversation manager
- **Server services** (`server/`): Dockerized STT (Whisper), TTS (Piper), Brain (Claude API)
- **Tests** (`tests/`): pytest suite, mocking, integration tests
- **Scripts** (`scripts/`): Hardware test utilities
- **Web UI** (`src/emiglio/web/static/`): Browser-based control interface
- **Deployment** (`deploy/`): Systemd service, setup scripts, Docker compose
- **Dependencies**: `pyproject.toml`, Dockerfiles, requirements files

## What's Out of Scope

- Circuit design and wiring diagrams (→ `develop-electronics`)
- Physical assembly instructions (→ `develop-assembly`)
- AI/ML experimentation and prompt research (→ `develop-ai-skills`)
- Merging into `develop` (→ PM agent handles this)

## Current State

All 5 phases are complete. 31 tests passing. The codebase is functional end-to-end in mock mode. Key areas for improvement:

- Conversation memory / persistence
- Web UI polish (PWA, better mobile UX)
- Error handling hardening
- Server service health monitoring
- Integration test coverage
- Wake-word detection support
- Configuration validation and documentation

## Conventions

- Follow existing patterns in the codebase (see root `CLAUDE.md`)
- All subsystem communication through `EventBus` — no direct coupling
- `asyncio` throughout, no blocking calls on main thread
- Config via env vars with `EMIGLIO_` prefix using `pydantic-settings`
- Test with `pytest-asyncio` in auto mode, mock hardware in conftest
- Use `uv` for dependency management
- Commit messages should be descriptive and prefix with the subsystem area (e.g., "audio: add wake-word detection support")

## Coordination

When your work is ready for review, ensure:
1. All tests pass (`uv run pytest`)
2. Mock mode still works (`EMIGLIO_HARDWARE_MODE=mock uv run python -m emiglio`)
3. Commit your changes to `develop-software`
4. The PM agent on `develop` will handle merging
