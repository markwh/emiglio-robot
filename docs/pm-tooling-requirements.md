# PM Tooling for Requirements Tracking

Design notes for extending `emiglio-pm` / `worktree-pm` with milestone and requirements tracking.

## Motivation

The PM agent needs to:
1. Track v1.0 requirements to completion against a deadline
2. Capture v2.0+ ideas without losing them or letting them creep into v1.0
3. Surface blockers and critical-path items during `sitrep`
4. Let workstream agents see which requirements are assigned to them

## Data Model

### `requirements.yml` (new file, repo root)

Separate from `workstreams.yml` to keep concerns clean. The workstream manifest defines *who works on what*; the requirements file defines *what needs to be done*.

```yaml
milestones:
  v1.0:
    description: Working robot — moves, sees, hears, speaks, converses
    deadline: null  # set by Mark when ready
    acceptance:
      - Plug in wall adapter, SSH into Pi
      - Run emiglio, open web UI on phone
      - Drive with joystick
      - Voice conversation (push-to-talk → STT → Brain → TTS → speaker)
      - "What do you see?" gets camera-aware response
      - Emiglio personality (retro-optimist, 1-3 sentences)

  v2.0:
    description: Untethered + expanded capabilities
    deadline: null
    acceptance: []

requirements:
  HW-01:
    title: Pi 5 mounted in body (canister sled)
    milestone: v1.0
    workstream: assembly
    status: not_started  # not_started | in_progress | done | blocked
    blocked_by: []
    tags: [hardware, critical-path]
    notes: "Needs canister, M2.5 standoffs"

  # ... (all requirements from v1-requirements.md)

parking_lot:
  - title: Battery power (LiPo or USB power bank)
    category: hardware
    complexity: medium
    milestone: v2.0
    notes: "Eliminates wall tether"

  - title: Projector display
    category: hardware
    complexity: medium
    milestone: v2.0
    notes: "$40 projector already purchased"

  # ... (ideas list)
```

### Why YAML, not a database

- Version-controlled alongside code
- Human-readable and hand-editable
- Agents can read/write it with standard tools
- Diffs are meaningful in PRs
- No infrastructure to maintain

## Proposed CLI Commands

### `emiglio-pm req list`

List requirements, filterable by milestone, workstream, status, tag.

```bash
emiglio-pm req list                          # all v1.0 requirements
emiglio-pm req list --milestone v2.0         # v2.0 parking lot
emiglio-pm req list --workstream assembly    # assembly team's requirements
emiglio-pm req list --status blocked         # show blockers
emiglio-pm req list --tag critical-path      # critical path items
```

Output: table with ID, title, status, workstream, blocked_by.

### `emiglio-pm req status`

Dashboard view — summary counts by workstream and milestone, critical-path progress bar, blockers highlighted.

```
v1.0 Progress: ████████████░░░░░░░░ 23/41 (56%)

  Assembly:     ░░░░░░░░░░░░░░░░░░░░  0/10
  Electronics:  █████░░░░░░░░░░░░░░░  1/4
  Software-Pi:  ████████████████░░░░ 12/16
  Software-Srv: ████████████████████  6/6
  AI:           ████████████████░░░░  4/5

Blockers: 4
  HW-01: Pi 5 mounted in body — needs canister, standoffs
  HW-02: TB6612FNG wired — needs parts order
  ...

Critical path: Parts procurement → Bench test → Assembly → Integration
```

### `emiglio-pm req update <id> [--status <s>] [--notes <n>]`

Update a requirement's status or notes.

```bash
emiglio-pm req update HW-01 --status in_progress
emiglio-pm req update HW-01 --status done --notes "Mounted 2026-03-15"
```

### `emiglio-pm req add <title> --milestone <m> --workstream <w>`

Add a new requirement.

```bash
emiglio-pm req add "LED eye GPIO pin assignment" --milestone v1.0 --workstream electronics --tag critical-path
```

### `emiglio-pm req park <title> [--category <c>] [--complexity <x>]`

Add an idea to the parking lot without it being a tracked requirement. Quick capture for when ideas proliferate.

```bash
emiglio-pm req park "Home Assistant integration" --category software --complexity medium
```

### `emiglio-pm req check`

Validation: ensure all requirements reference valid workstreams and milestones, no orphaned blocked_by references, no done items still listed as blockers.

## Integration with Existing Commands

### `sitrep` enhancement

Add a requirements section to the existing `sitrep` output:

```
=== Requirements (v1.0) ===
  assembly:    0/10 done, 0 in progress, 2 blocked
  electronics: 1/4 done, 0 in progress, 0 blocked
  software:   18/22 done, 0 in progress, 4 blocked on Pi hardware
  ai-skills:   4/5 done, 0 in progress, 1 blocked on integration

  Deadline: 2026-04-01 (24 days remaining)
  Blockers: Parts procurement (10 items to order)
```

### `WORKTREE.md` enhancement

Embed each workstream's assigned requirements in the generated WORKTREE.md so agents can see their work items:

```markdown
## Your Requirements (v1.0)

| ID | Title | Status |
|----|-------|--------|
| HW-01 | Pi 5 mounted in body | not_started |
| HW-02 | TB6612FNG wired | not_started |
...
```

## Implementation Plan

This would go in the `develop-pm-decouple` or `develop-software` workstream:

1. **Data model** — Add `RequirementsManifest` dataclass to `manifest.py` (or new `requirements.py`)
2. **YAML I/O** — Load/save `requirements.yml` with validation
3. **CLI commands** — Add `req` subcommand group to `cli.py`
4. **Sitrep integration** — Extend `git_ops.sitrep()` to include requirement counts
5. **WORKTREE.md integration** — Extend Jinja2 template to embed requirements
6. **Seed data** — Generate initial `requirements.yml` from `docs/v1-requirements.md`

### Generalization for worktree-pm

Since `pm-decouple` is extracting a generic `worktree-pm` package, the requirements layer should be designed generically:

- Milestones, requirements, parking lot are project-agnostic concepts
- The YAML schema shouldn't reference emiglio-specific fields
- Workstream references should be validated against `workstreams.yml` but the requirements system doesn't depend on workstream internals
- The `req` commands work standalone — you don't need worktrees to use requirements tracking
