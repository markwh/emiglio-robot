# Finding: One-Way Clutch on Drive Axle

**Date:** 2026-03-01
**Found by:** Mark (during base inspection)
**Status:** RESOLVED — clutch removed, wheels now fully independent

## Observation

The wheelshaft has a ratchet joint at the center where the left and right axle halves meet. The ratchet teeth are part of the same plastic piece as the axle gear (not a separate insert).

### Original behavior (corrected understanding)

The single ratchet direction meant:
- **One wheel locks to the center coupling in forward rotation**
- **The other wheel locks in reverse rotation**
- (Because the wheels are on opposite sides, "forward travel" means opposite rotations at the center joint)

This created **asymmetric, direction-dependent coupling** — a crude straight-line stability mechanism for the original toy. It made left turns behave differently from right turns and complicated software-based differential steering.

## Resolution

**Option A was chosen: remove the clutch teeth.**

The ratchet teeth on the center joint were ground down, decoupling the left and right axle halves entirely. Each motor now independently drives its own wheel in both directions.

**Result:** Both wheels freely rotate independently in both directions. Full differential drive is available. The existing software (`MotorDriver`, joystick mapping, `MOVE_PRESETS`) works as designed with no modifications needed.

## Impact on Other Workstreams

### Software (`develop-software`) — NO IMPACT (resolved)

The clutch removal means the software's assumptions are correct as-is:
- Bidirectional motor control works: `[-1.0, 1.0]` range per motor
- Pivot turns work: opposite motor directions for tight turning
- Backward drive works: both motors negative
- Joystick mapping works: full X/Y range

No code changes needed.

### Electronics (`develop-electronics`) — NO IMPACT

No circuit changes. TB6612FNG drives motors bidirectionally as planned.

### Assembly (`develop-assembly`) — DOCUMENTED

Modification is complete and irreversible. The axle halves stay butted together at the center but are no longer mechanically coupled.

## Work Log

| Date | Action |
|------|--------|
| 2026-03-01 | Base opened, internals inspected |
| 2026-03-01 | Gearbox lubricated with grease — grinding noise resolved |
| 2026-03-01 | One-way clutch discovered at center axle joint |
| 2026-03-01 | Clutch mechanism analyzed — asymmetric directional coupling confirmed |
| 2026-03-01 | Ratchet teeth ground down — wheels now fully independent |
| 2026-03-01 | 5V breadboard supply tested — insufficient for motors; use D cells or 12V |

## Notes

- 5V breadboard supply was insufficient to drive motors (feeble motion, sparking at terminals) — use D cells or 12V adapter for proper motor testing
- Gearbox runs smoothly after lubrication
- Axle halves still sit together at center; monitor for lateral play — add a thrust washer if they start sliding apart
