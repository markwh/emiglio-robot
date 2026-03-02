# Emiglio Robot

AI-powered vintage Emiglio toy robot. Split architecture: Raspberry Pi 4B (edge I/O) + Linux home server (inference).

## Dev Setup

```bash
uv sync
uv run python -m emiglio          # starts the Pi-side app
uv run pytest                     # run tests
uv run emiglio-pm status          # show worktree status
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
workstreams.yml        # Workstream manifest (branches, scopes, metadata)
src/emiglio/           # Pi-side package (installed as 'emiglio')
  event_bus.py         # Async pub/sub event system
  config.py            # Pydantic settings
  models.py            # Event and command dataclasses
  locomotion/          # Motor control
  vision/              # Camera + MJPEG streaming
  audio/               # Mic capture + speaker playback
  web/                 # FastAPI server + static UI
src/emiglio_pm/        # PM tooling CLI (dev-only)
  cli.py               # argparse + command dispatch
  manifest.py          # Load/validate workstreams.yml
  git_ops.py           # Git worktree/merge/rebase helpers
  worktree_md.py       # Jinja2 WORKTREE.md generation
server/                # Home server Docker services
scripts/               # Hardware test scripts
tests/                 # pytest tests
docs/                  # Project documentation
  electronics/         # Circuit design, wiring, components
  assembly/            # Physical build guides and plans
  ai-skills/           # AI/ML research and experiment notes
  workstreams/         # Agent instruction files (source for WORKTREE.md)
notebooks/             # Jupyter notebooks for AI experiments
```

## Workstream / Worktree Workflow

This project uses **git worktrees** for parallel development across workstreams. Configuration lives in `workstreams.yml` at the repo root. Each worktree gets a generated `WORKTREE.md` with scoped agent instructions.

### Branches

- `main` — stable releases (merge from `develop` after review)
- `develop` — integration branch (PM agent lives here)
- `develop-software` — Pi-side + server-side code
- `develop-electronics` — circuit design, wiring, components
- `develop-assembly` — physical robot build docs
- `develop-ai-skills` — AI/ML experiments, prompt engineering

### Worktree Locations

All worktrees live under `.claude/worktrees/{name}/`. Each contains a generated `WORKTREE.md` (gitignored — source of truth is `workstreams.yml` + `docs/workstreams/{name}.md`).

### PM CLI (`emiglio-pm`)

```bash
uv run emiglio-pm status          # show all worktrees: exists, dirty, WORKTREE.md, latest commit
uv run emiglio-pm create <name>   # git worktree add + generate WORKTREE.md
uv run emiglio-pm sync <name>     # regenerate WORKTREE.md in one worktree
uv run emiglio-pm sync-all        # regenerate WORKTREE.md in all worktrees
uv run emiglio-pm merge <name>    # merge workstream branch into develop
uv run emiglio-pm rebase-all      # rebase all worktree branches onto develop
```

### Coordination

- The **PM agent** on `develop` manages worktrees via `emiglio-pm` and merges completed work.
- **Workstream agents** commit to their own branches and flag readiness.
- Merges into `develop` are handled by the PM agent.
- Merges from `develop` into `main` happen during periodic reviews with Mark.
- If a `WORKTREE.md` exists in your repo root, follow its instructions for your workstream scope.
