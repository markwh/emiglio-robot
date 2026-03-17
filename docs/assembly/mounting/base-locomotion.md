# Base / Locomotion Mounting Plan

## Overview

The locomotion base is the black plastic GP Toys platform that forms the robot's bottom section. It contains the existing drive system: two DC motors driving the main wheels independently (differential drive), plus stabilizer wheels for balance. This is the most mechanically complete section of the robot — the motors and gearbox are already in place from the original toy.

The base also includes **two D-cell battery cases** (4 D batteries total) and a **12V DC input port** from the original toy — both reusable for motor power.

The main assembly work here is:
1. Reconnect the existing motors to new wiring (originals were clipped)
2. Mount the TB6612FNG motor driver board
3. Wire the existing D-cell battery cases (or 12V port) to the TB6612FNG for motor power
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

### 2. D-Cell Batteries / 12V DC Port (Motor Power)

**What's already there:** The base has two D-cell battery cases (4 D cells total) and a 12V DC input port, both from the original toy. These provide motor power.

**D-cell advantages over AA:** D cells have ~5-10x the capacity of AAs (~12,000 mAh vs. ~2,000 mAh) and handle high current draws from motors much better. Reusing the existing cases means no new battery holder needed.

**Why separate power:** Motors draw high current with spikes during stall/startup. Separate battery power isolates the Pi from motor noise and voltage drops. The TB6612FNG's VM (motor voltage) pin connects to the battery supply, while its VCC (logic voltage) connects to 3.3V from the Pi.

**Power options:**
1. **D-cell batteries** (portable, already installed) — trace the wiring to determine voltage (likely 6V if 4 cells in series)
2. **12V DC adapter** through the existing port (unlimited runtime for bench testing) — verify the port wiring goes to the motor circuit
3. **Both** — use batteries for mobile testing, 12V adapter for bench sessions

**Measurements needed:**
- [ ] Battery case wiring: series (6V) or parallel (3V)? — trace wires or measure with multimeter
- [ ] 12V port wiring: where do its leads connect?
- [ ] Available space in base interior next to motors (L x W x H in mm)

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
| Left motor control (3 wires) | 26 AWG signal wire | AIN1, AIN2, PWMA |
| Right motor control (3 wires) | 26 AWG signal wire | BIN1, BIN2, PWMB |
| VCC (2 wires, duplicated) | 26 AWG | 3.3V logic power from Pi (one per connector) |
| GND (2 wires, duplicated) | 22 AWG | Common ground (one per connector) |

**Total:** 10 wires across 2x JST-XH 5-pin connectors (see connector strategy below).

Battery GND ties to Pi GND through the base breadboard GND rail, which connects to both JST-XH GND pins.

### Connector strategy

**2x JST-XH 5-pin connectors**, split by motor side:

- **5-pin "L":** AIN1, AIN2, PWMA, VCC, GND (left motor control + power)
- **5-pin "R":** BIN1, BIN2, PWMB, VCC, GND (right motor control + power)

**Why this design:**
- Each connector is self-contained per motor side — debug or disconnect one side independently
- Redundant VCC/GND on both connectors for robust power delivery
- Symmetric pinout (same layout, left vs right)
- Avoids 6-pin JST-XH, which is used for the head LED connector — prevents accidental swap
- JST-XH connectors are polarity-keyed to prevent misconnection

```
        BODY INTERIOR (webcam box)
        ┌─────────────────────┐
        │                     │
        │  Pi GPIO ──────┐    │
        │  Pi 3.3V ──┐   │   │
        │  Pi GND ─┐  │   │   │
        │          │  │   │   │
        └──────────┼──┼───┼───┘
                   │  │   │
          ═══ 2x JST-XH 5p ═══  ← base-to-body interface
              "L"       "R"
                   │  │   │
        ┌──────────┼──┼───┼───┐
        │          │  │   │   │
        │      TB6612FNG      │  BASE INTERIOR
        │       │      │      │
        │    Motor L  Motor R │
        │                     │
        │    [4xD battery]    │
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
| Motor power | 4xD battery pack (6V) | High capacity, reuses existing D-cell cases, isolates motors from Pi power |
| Battery mounting | Velcro in base | Easy battery changes without opening base |
| Base-to-body connector | 2x JST-XH 5-pin (left + right motor sides) | Per-side independence, avoids 6-pin confusion with head LED connector, polarity-keyed |
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
