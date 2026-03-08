## Your Role

You are decoupling the PM agent tooling (`emiglio_pm`) into a standalone, project-agnostic package called `worktree-pm`. The goal is a general-purpose CLI that any project can adopt by adding a `workstreams.yml` to its repo root — enabling the same multi-agent worktree workflow that emiglio-robot uses.

This is the first spinoff from emiglio-robot, and it sets the pattern for future spinoffs. Move deliberately. Each change should be small, inspectable, and tested against emiglio-robot's real workflow before proceeding.

## Two-Repo Setup

The work spans two repositories connected by a symlink:

```
~/Documents/projects/worktree-pm/          # standalone repo (the new home)
  src/emiglio_pm/                          # source code lives HERE
  pyproject.toml                           # standalone: jinja2 + pyyaml only
  tests/

~/Documents/projects/emiglio-robot/        # consuming project
  src/emiglio_pm -> worktree-pm/src/...    # SYMLINK to standalone source
  pyproject.toml                           # still lists emiglio-pm as a script
  workstreams.yml                          # project-specific config
```

**Edits to `src/emiglio_pm/`** pass through the symlink — the files physically live in worktree-pm. Commit code changes in worktree-pm. Commit integration changes (pyproject.toml, workstreams.yml, CLAUDE.md) in emiglio-robot on `develop-pm-decouple`.

## What Needs to Change

### Emiglio-specific code to generalize

| File | What | Notes |
|------|------|-------|
| `cli.py` | `"Emiglio workstream management CLI"` | Generic description |
| `cli.py` | CLI entry point name `emiglio-pm` | Rename to `wt-pm` (both repos' pyproject.toml) |
| `git_ops.py` | `_is_conda_venv()` | Remove — emiglio debugging artifact |
| `git_ops.py` | `status_all()` references to conda | Remove |
| `shell_init.py` | `EMIGLIO_WEB_PORT` env var | Generalize to configurable env var or remove |
| `shell_init.py` | `"emiglio"` in titles/comments | Derive from project name or workstreams.yml |
| `manifest.py` | Package name `emiglio_pm` | Rename to `worktree_pm` (last step — most disruptive) |

### New capabilities for standalone use

- A `CLAUDE.md` for worktree-pm itself, defining the PM agent's identity when dropped into a new project
- Tests that run against a temp git repo with a synthetic `workstreams.yml` (no emiglio dependency)
- A `wt-pm init` command to bootstrap `workstreams.yml` in a new project

### Integration changes in emiglio-robot

- Update `pyproject.toml` script entry point when CLI name changes
- Eventually: replace symlink with a real package dependency (`worktree-pm` from PyPI or git)

## Guiding Principles

1. **One thing at a time.** Each change is a single commit, tested before moving on.
2. **Don't break emiglio-robot.** After every change, verify with `emiglio-pm sitrep` (or `wt-pm sitrep` post-rename) from emiglio-robot's root.
3. **Generalize by removing, not abstracting.** Prefer deleting emiglio-specific code over adding configuration layers. If something isn't needed for the general case, drop it.
4. **The package rename (`emiglio_pm` -> `worktree_pm`) comes last.** It touches every import and both repos' configs. Do it only after everything else is clean.
5. **Tests before features.** The standalone repo has no tests yet. Adding test infrastructure early means every subsequent change can be validated.

## Suggested Order of Operations

1. Add test infrastructure to worktree-pm (temp git repo fixture, basic CLI smoke tests)
2. Remove `_is_conda_venv()` and conda references
3. Generalize `shell_init.py` (remove emiglio-specific env var and strings)
4. Generalize CLI description and strings
5. Write worktree-pm's own `CLAUDE.md`
6. Add `wt-pm init` command
7. Rename CLI entry point: `emiglio-pm` -> `wt-pm`
8. Rename package: `emiglio_pm` -> `worktree_pm`
9. Replace symlink with real dependency in emiglio-robot

## Coordination

- Changes to `src/emiglio_pm/` affect ALL emiglio-robot workstreams (they all use the PM CLI). Test broadly.
- The PM agent on `develop` uses this tooling live — breaking changes disrupt the whole workflow.
- Commit code changes in **worktree-pm** repo. Commit emiglio-robot integration changes on **develop-pm-decouple**.
