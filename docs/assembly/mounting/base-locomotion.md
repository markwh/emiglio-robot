# Base / Locomotion Mounting Plan

## Overview

The locomotion base is the black plastic GP Toys platform that forms the robot's bottom section. It contains the existing drive system: two DC motors driving the main wheels independently (differential drive), plus stabilizer wheels for balance. This is the most mechanically complete section of the robot — the motors and gearbox are already in place from the original toy.

The main assembly work here is:
1. Reconnect the existing motors to new wiring (originals were clipped)
2. Mount the TB6612FNG motor driver board
3. Mount or route the 4xAA battery pack for motor power
4. Establish the cable interface between the base and the body above

### Reference Frames

| Frame | What it shows |
|-------|---------------|
| `frame_0004.jpg` | Full robot assembled — black base platform visible, GP Toys sticker, body + head on top |
| `frame_0015.jpg` | **Base interior** — two DC motors with red/black wiring, central mounting bracket, wheel drive mechanism, stabilizer wheel housings |
| `frame_0020.jpg` | Body sitting on base (no head) — shows how body barrel mates with base top |
| `frame_0025.jpg` | Same, different angle — GP Toys sticker visible on base front |

## Base Anatomy

### Top-down view (cover removed)

```
    FRONT
┌─────────────────────────────┐
│  ○ stabilizer               │
│    wheel                    │
│                             │
│  ┌───────────────────────┐  │
│  │      motor bracket     │  │
│  │  ┌─────┐   ┌─────┐   │  │
│  │  │ MOT │   │ MOT │   │  │
├──┤  │  L  ├─●─┤  R  │   ├──┤
│  │  └─────┘   └─────┘   │  │  ● = central divider
│W │                       │ W│  W = drive wheels (outside)
│  └───────────────────────┘  │
│                             │
│  ○ stabilizer               │
│    wheel                    │
└─────────────────────────────┘
    REAR
```

### Side profile

```
         body barrel sits here
         ─────────────────────
        │                     │ ← base top surface (flat)
        │  [motors]  [batt?]  │ ← internal cavity
        └──┤wheel├──────┤wheel├┘
           └─────┘      └─────┘
            ○                ○   ← stabilizer wheels (casters)
        ═══════════════════════  ← floor
```

### Key features (from frame_0015)

- **Two DC motors** mounted side by side on a central metal/plastic bracket
- Motors are cylindrical, ~25-30 mm diameter, oriented perpendicular to the direction of travel
- White plastic gear couplings connect each motor shaft to the drive wheels via a simple gearbox
- **Central divider** bracket separates and supports the two motors
- **Red/black wires** visible on at least one motor (the originals — these were clipped during disassembly)
- **Two stabilizer wheels** in circular housings at front and rear of the base — likely small casters or ball casters
- **Access panel** on the bottom (screws visible in frame_0015) for servicing the motor compartment
- **GP Toys** sticker on the front edge of the base

## Components to Mount

### 1. TB6612FNG Motor Driver Board

**What it is:** A dual H-bridge motor driver IC on a small breakout board (~20x25 mm). Drives two DC motors independently with PWM speed control and direction.

**Position:** Inside the base, near the motors.

**Why in the base:** Minimizes motor wire length (reduces electrical noise), keeps high-current motor wiring short, and keeps the base self-contained as a locomotion module.

**Mounting approach:**
- Mount the TB6612FNG breakout board on the inner wall of the base using double-sided foam tape or a small standoff
- Position it near the motor bracket where the motor wires can easily reach
- Keep it away from the gear mechanism to avoid getting snagged
- The board is small enough to fit in the gap between the motor bracket and the base wall

**Alternative:** Mount the TB6612FNG in the body instead, on the breadboard with the Pi. This simplifies the base (only raw motor wires come up) but means longer motor power wires and more cables between base and body. **Recommended: mount in the base.**

### 2. 4xAA Battery Pack (Motor Power)

**What it is:** A holder for 4 AA batteries providing ~6V to power the motors through the TB6612FNG.

**Position:** Inside the base, in the available space next to or below the motors.

**Why separate power:** Motors draw high current with spikes during stall/startup. Separate battery power isolates the Pi from motor noise and voltage drops. The TB6612FNG's VM (motor voltage) pin connects to the battery pack, while its VCC (logic voltage) connects to 3.3V from the Pi.

**Mounting approach:**
- Check if the original battery compartment exists (many vintage toys had one in the base)
- If yes, reuse it — just wire it to the TB6612FNG VM pin
- If no built-in compartment, mount the 4xAA holder with double-sided tape or Velcro on the base interior floor
- Velcro is preferable — makes battery changes easy without opening the base
- Route battery wires to the TB6612FNG board

**Alternative power:** A small LiPo pack with a voltage regulator could replace AAs for longer runtime, but adds charging complexity. AAs are simpler for v1.0.

**Measurements needed:**
- [ ] Available space in base interior next to motors (L x W x H in mm)
- [ ] Whether original toy had a battery compartment in the base
- [ ] 4xAA holder dimensions vs. available space

### 3. Motor Wires (Existing)

**What they are:** The red/black wires already soldered to each motor's terminals.

**Current state:** The original wires were clipped during disassembly. They need to be either:
- Stripped and extended with new wire to reach the TB6612FNG, or
- Replaced entirely by soldering new wires to the motor terminals

**Approach:**
- Inspect the remaining motor wire stubs — if long enough (~30-50 mm remain), strip and solder extensions
- If too short, desolder the stubs and solder fresh 22 AWG stranded wire directly to motor terminals
- Each motor needs 2 wires (motor+ and motor-)
- Label left vs. right motor wires clearly (tape flags or different colored heat shrink)

## Cable Routing: Base → Body

The base and body are separate sections that stack. Cables need to pass between them.

### Cables passing between base and body

| Cable | Type | Purpose |
|-------|------|---------|
| TB6612FNG control (6 wires) | 26 AWG signal wire | 3x per motor: forward, backward, enable (PWM) |
| TB6612FNG logic power | 2 wires, 26 AWG | VCC (3.3V) + GND from Pi |
| Motor battery GND | 1 wire, 22 AWG | Common ground between motor battery and Pi |

**If TB6612FNG is mounted in the base** (recommended):
- 6 GPIO signal wires + 2 power wires + 1 common GND = **9 thin wires** pass from base to body
- These can be bundled into a ribbon or use a single multi-pin connector

**If TB6612FNG is mounted in the body instead:**
- 4 motor power wires (2 per motor, 22 AWG — carrying motor current) pass from base to body
- Plus battery power wires if battery is in the base
- Thicker wires, more current, more noise — less ideal

### Connector strategy (recommended)

Use a connector at the base-to-body interface so the sections can separate:

**Option A: Multi-pin header connector**
- 10-pin (or 2x5) dupont/JST connector
- Carries all 9 signal + power wires in one plug
- Clean, single disconnect point

**Option B: Screw terminal block**
- Mounted at the top edge of the base
- Easy to wire/rewire during prototyping
- Not as clean for disconnect but very forgiving

**Recommended for prototyping:** Option B (screw terminals) initially, migrate to Option A (multi-pin connector) once wiring is finalized.

```
        BODY INTERIOR
        ┌─────────────────────┐
        │                     │
        │  Pi GPIO ──────┐    │
        │  Pi 3.3V ──┐   │   │
        │  Pi GND ─┐  │   │   │
        │          │  │   │   │
        └──────────┼──┼───┼───┘
                   │  │   │
          ═══ CONNECTOR ═══  ← base-to-body interface
                   │  │   │
        ┌──────────┼──┼───┼───┐
        │          │  │   │   │
        │      TB6612FNG      │  BASE INTERIOR
        │       │      │      │
        │    Motor L  Motor R │
        │                     │
        │    [4xAA battery]   │
        └─────────────────────┘
```

## Physical Measurements Checklist

Before starting assembly, measure and record these on the physical base:

### Base exterior
- [ ] Base platform overall dimensions (L x W x H in mm)
- [ ] Distance from base top surface to floor (ground clearance)
- [ ] Drive wheel diameter (mm)
- [ ] Stabilizer wheel diameter (mm)
- [ ] Location and size of any existing cable pass-through holes in base top

### Base interior
- [ ] Internal cavity dimensions (L x W x H in mm)
- [ ] Motor bracket dimensions and position
- [ ] Available free space beside/around motors for TB6612FNG and battery pack
- [ ] Motor terminal wire stub lengths (mm remaining after clip)
- [ ] Whether original battery compartment exists, and its dimensions
- [ ] Access panel screw type and count (for reassembly)

### Motors
- [ ] Motor body diameter (mm)
- [ ] Motor voltage rating (likely 3-6V, but verify)
- [ ] Motor stall current (if markings visible, or measure with bench supply)
- [ ] Motor terminal type (solder pads, tabs, etc.)

## Design Decisions Log

| Decision | Choice | Why |
|----------|--------|-----|
| TB6612FNG location | In the base | Short motor wires, less noise, base is self-contained locomotion module |
| Motor power | 4xAA battery pack (6V) | Simple, replaceable, isolates motors from Pi power |
| Battery mounting | Velcro in base | Easy battery changes without opening base |
| Base-to-body connector | Screw terminals (prototype) → multi-pin (final) | Screw terminals are forgiving during prototyping |
| Motor wires | Extend or replace existing | Inspect stubs first — extend if possible, replace if too short |
| Common ground | Single wire between battery GND and Pi GND | Required for TB6612FNG logic to reference Pi signal levels |

## Risks and Considerations

### Weight distribution
- The battery pack adds significant weight to the base — this is actually good (low center of gravity)
- Ensure batteries are centered to avoid tipping

### Motor current
- The TB6612FNG handles up to 1.2A continuous per channel (3.2A peak)
- If the original Emiglio motors draw more than this at stall, the TB6612FNG will thermal-shutdown
- Measure stall current before committing — if too high, consider an L298N driver instead (handles 2A continuous) or add current limiting in software (PWM cap)

### Gear noise
- The original gearbox may be noisy — this can interfere with the microphone in the head
- Not an assembly issue per se, but worth noting: silicone grease on the gears may help
- The physical separation (base → body → head) provides some acoustic isolation

### Floor clearance
- With the body and head stacked on top, the robot is quite tall relative to its base
- If it tips over on uneven surfaces, adding wider stabilizer wheels or a skirt could help
- For v1.0, operate on flat floors (the foam puzzle mat in the workspace is ideal for testing)
