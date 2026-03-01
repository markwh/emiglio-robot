# Finding: One-Way Clutch on Drive Axle

**Date:** 2026-03-01
**Found by:** Mark (during base inspection)
**Status:** NEEDS VERIFICATION — see tests below

## Observation

The wheelshaft has a joint at the center where the left and right axles meet. This joint:
- **Locks the wheels to motor drive in the forward direction** — full power transfer
- **Allows independent wheel motion in reverse** — wheels freewheel, motors don't drive

This is a **one-way clutch** (overrunning clutch / freewheel), common in toy drive systems. Its original purpose was to let the toy be pushed by hand without fighting gearbox resistance.

## Impact on Other Workstreams

### Software (`develop-software`) — HIGH IMPACT

The locomotion code assumes **bidirectional motor control**:

| Feature | Current assumption | Actual behavior (if clutch confirmed) |
|---------|-------------------|--------------------------------------|
| `set_motors(-0.5, -0.5)` backward | Both wheels drive backward | Motors spin but wheels don't drive — **no reverse** |
| `"left": (-0.5, 0.5)` turn preset | Left backward + right forward = tight left turn | Left wheel freewheels, only right drives — **wide arc, not pivot** |
| `"right": (0.5, -0.5)` turn preset | Right backward + left forward = tight right turn | Right wheel freewheels, only left drives — **wide arc, not pivot** |
| `"forward": (0.6, 0.6)` | Both wheels forward | Works as expected |
| Joystick Y-axis negative | Backward motion | **No effect** |

**Required software changes if clutch is confirmed:**
- Remove or remap backward movement commands
- Change turning strategy: instead of opposite-direction motors, use **differential forward speed** (e.g., turn left = left motor slow, right motor fast — both forward)
- Update `MOVE_PRESETS` to forward-only turning:
  ```python
  MOVE_PRESETS = {
      "forward": (0.6, 0.6),
      "backward": (0.0, 0.0),   # or very slow forward?
      "left": (0.1, 0.6),       # left slow, right fast
      "right": (0.6, 0.1),      # left fast, right slow
      "stop": (0.0, 0.0),
  }
  ```
- Update joystick mapping to only use forward + differential turning
- Consider: can the robot "reverse" by doing a U-turn instead?

### Electronics (`develop-electronics`) — LOW IMPACT

No circuit changes needed. The TB6612FNG still drives the motors the same way — the clutch is purely mechanical. The H-bridge will still send reverse voltage to the motors; the motors will spin backward; the clutch will just disengage.

One consideration: if the motor spins freely in reverse (no load), it draws very little current — not a problem, but good to know for power budgeting.

### Assembly (`develop-assembly`) — MEDIUM IMPACT

- Document the clutch mechanism location and behavior
- Investigate whether the clutch can be **removed or bypassed** to enable full bidirectional drive
- If removal is possible without destroying the gearbox, this is the preferred fix — it restores full differential-drive capability
- Photograph the clutch mechanism for reference

## Verification Tests

Perform these tests and record results:

### Test 1: Forward drive
- [ ] Apply battery power to motor (forward polarity)
- [ ] Result: wheel drives forward? Y/N
- [ ] Both motors? Y/N

### Test 2: Reverse drive
- [ ] Apply battery power to motor (reversed polarity)
- [ ] Result: motor shaft spins? Y/N
- [ ] Result: wheel drives backward? Y/N
- [ ] Or does wheel stay still / freewheel? Y/N

### Test 3: Hand rotation
- [ ] Turn wheel by hand in forward direction
- [ ] Result: resistance (locked to gearbox)? Y/N
- [ ] Turn wheel by hand in reverse direction
- [ ] Result: freewheels (no resistance)? Y/N

### Test 4: Clutch inspection
- [ ] Can you see the clutch mechanism? Where exactly is it?
- [ ] Is it a ratchet, sprag clutch, or roller clutch?
- [ ] Does it look removable/bypassable without destroying the gearbox?
- [ ] Photograph the mechanism

## Resolution Options

| Option | Effort | Result |
|--------|--------|--------|
| **A: Remove/bypass the clutch** | Medium (mechanical work) | Full bidirectional drive — best outcome, existing software works as-is |
| **B: Modify software for forward-only** | Low (code changes) | Robot can only go forward + arc turns — limited but functional |
| **C: Replace gearbox/wheels** | High (sourcing parts, custom mounting) | Full control but significant rework |

**Recommended:** Try option A first. If the clutch is a removable insert (common in toys — often a small plastic ratchet disc), popping it out may be straightforward. If it's integral to the gear train, fall back to option B.

## Notes

- Gearbox has been lubricated with silicone/lithium grease (2026-03-01)
- Some grinding noise was observed before lubrication — improved after
- 5V breadboard supply was insufficient to drive motors (feeble motion) — use D cells or 12V adapter for testing
