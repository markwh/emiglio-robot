# Head Component Mounting Plan

## Overview

The Emiglio head is a white plastic dome with a dark tinted visor, a flip-up top section, and a carry handle on top. It houses the robot's primary I/O: camera, microphone, speaker, and (future) projector.

The head sits on the body barrel's open rim and was originally secured with screws. All original wiring has been clipped during disassembly.

### Reference Frames

| Frame | What it shows |
|-------|---------------|
| `frame_0005.jpg` | Side view — visor shape, speaker grilles on sides, handle on top |
| `frame_0010.jpg` | Front view, visor down — red LED glow visible through tinted visor |
| `frame_0036.jpg` | **Visor flipped up** — two red/pink eye lenses visible, interior cavity exposed |
| `frame_0045.jpg` | Mini projector held for size reference, arm parts in background |
| `frame_0020.jpg` | Body without head — open barrel rim where head sits |

## Head Anatomy

```
         ┌─── handle ───┐
         │   ┌───────┐   │
         └───┤ top   ├───┘    ← top plate with vent grilles
             │ plate │           (flips up to expose interior)
        ┌────┴───────┴────┐
        │                 │
        │   VISOR AREA    │  ← dark tinted plastic, ~180° front arc
        │  (eye lenses    │     two original eye lens positions
        │   behind here)  │     behind visor
        │                 │
        ├─────────────────┤  ← visor hinge line / chin
        │   lower ring    │
        │  (white plastic)│  ← solid white band below visor
        └────────┬────────┘
                 │
           neck opening       ← mates with body barrel rim
```

## Components to Mount

### 1. USB Webcam (Camera)

**Position:** Behind one of the two original eye lens positions.

**Why:** The eye lenses are already transparent/translucent red plastic — a camera placed behind one gets a natural forward-facing viewpoint at "eye level." The tinted visor may reduce light slightly but adds a cool aesthetic.

**Mounting approach:**
- Remove the original red lens from one eye socket (likely left eye, viewer's right)
- Size the opening — measure the inner diameter of the eye socket
- Mount a small USB webcam (board camera or stripped webcam) behind the opening
- Secure with hot glue, mounting putty, or a 3D-printed bracket
- If the red lens causes color cast / darkness issues, replace it with clear plastic or remove it entirely and rely on the tinted visor for aesthetics

**Cable:** USB cable routes down through the neck opening into the body to reach the Pi.

**Measurements needed:**
- [ ] Eye lens socket inner diameter (mm)
- [ ] Depth from lens socket to back wall of head cavity (mm)
- [ ] Chosen webcam board dimensions (mm)

### 2. USB Microphone

**Position:** Inside the head, near the top or front.

**Why:** Placing the mic high and forward minimizes motor noise pickup from the base. The head's plastic shell provides some acoustic isolation from the drive motors below.

**Mounting approach:**
- Small USB mic dongle or MEMS breakout board
- Mount near the top of the head cavity, possibly adhered to the underside of the flip-up top plate
- Alternatively, position near an existing vent grille on the side of the head for better sound pickup
- A small hole could be drilled if no existing openings provide adequate sound transmission

**Cable:** USB cable routes down through the neck opening.

**Acoustic considerations:**
- Keep mic as far as possible from the speaker to reduce feedback
- The flip-up top plate has vent grilles that may allow sound in
- Software echo cancellation will handle the rest (server-side)

**Measurements needed:**
- [ ] Vent grille opening dimensions on top plate (mm)
- [ ] Interior height from neck opening to top of dome (mm)
- [ ] Chosen mic module dimensions (mm)

### 3. Speaker

**Position:** Retain existing built-in speaker location.

**Why:** The original Emiglio already has a speaker mounted in the head with sound ports designed into the shell. Reusing this saves modification work and preserves the vintage look.

**Mounting approach:**
- Identify and test the existing speaker — determine if it's still functional and what impedance/wattage it is (likely 8Ω, 0.5-2W)
- If the original speaker is good, solder new wires to it (the originals were clipped)
- Wire to the PAM8403 amplifier board, which lives in the body (amp output wires route up through neck)
- If the original speaker is dead or too quiet, replace with a similarly sized unit

**Cable:** 2-wire speaker cable (amplified analog signal from PAM8403 in body) routes up through neck.

**Measurements needed:**
- [ ] Original speaker diameter and depth (mm)
- [ ] Speaker impedance (Ω) — measure with multimeter
- [ ] Speaker mounting screw positions (if any)

### 4. LED Eye(s)

**Position:** Behind the eye lens position not used by the camera (right eye from viewer's perspective).

**Why:** The original red LED eye glow is iconic. Keeping at least one LED eye preserves the vintage character. Could also add an LED behind the camera eye for a glowing-eye-with-camera effect.

**Mounting approach:**
- Simple red LED + resistor, driven from a Pi GPIO pin
- Or use an RGB LED / NeoPixel for programmable colors (status indication)
- Hot glue or friction-fit behind the lens

**Cable:** 2 thin wires (signal + ground) route through neck. Minimal space needed.

**Measurements needed:**
- [ ] Eye lens socket depth (mm) — same measurement as camera eye

### 5. Projector (v2.0 — Future)

**Position:** Inside head dome, lens aimed forward through visor opening.

**Why:** The flip-up visor reveals the interior — a projector mounted inside could project through this opening onto walls. This is a key differentiating feature.

**Mounting approach (deferred):**
- The mini projector (~$40 Amazon unit shown in frame_0045) physically fits inside the dome
- Would need the visor locked in the "up" position during projection
- Power and HDMI/USB cables route through neck
- This is a v2.0 feature — design the head cable routing with enough spare capacity for future projector cables

**Measurements needed (when ready):**
- [ ] Projector dimensions vs. head interior dimensions
- [ ] Projector lens offset from center
- [ ] Throw distance at typical wall distance

## Cable Routing: Head → Body

All cables from head components must pass through the neck opening where the head mates with the body barrel.

### Cables passing through neck

| Cable | Type | Purpose |
|-------|------|---------|
| USB (camera) | USB 2.0, thin cable | Video to Pi |
| USB (mic) | USB 2.0, thin cable | Audio input to Pi |
| Speaker wire | 2-conductor, ~22 AWG | Amplified audio from PAM8403 |
| LED wire | 2-conductor, ~26 AWG | GPIO signal + ground |
| **Future:** HDMI | Mini/micro HDMI | Projector video |
| **Future:** USB power | USB cable | Projector power |

**Total for v1.0:** 2 USB cables + 2 pairs of thin wire = manageable bundle.

### Routing strategy

```
        HEAD INTERIOR
        ┌─────────────────────┐
        │  [cam] [mic]  [LED] │
        │    │     │      │   │
        │    └──┬──┘      │   │
        │       │    ┌────┘   │
        │       │    │        │
        └───────┼────┼────────┘
                │    │
          ══════╪════╪══════  ← neck opening (body barrel rim)
                │    │
        ┌───────┼────┼────────┐
        │       │    │        │
        │    [Pi USB ports]   │  BODY INTERIOR
        │    [PAM8403 out]────┘  (speaker wire)
        │    [GPIO pin]───────┘  (LED wire)
        └─────────────────────┘
```

**Key considerations:**
- Bundle cables together with a small cable tie or spiral wrap just above the neck opening
- Leave ~50 mm (2") of slack inside the head for serviceability
- Use a strain relief point at the neck opening (zip tie anchor, adhesive cable clip, or hot glue saddle) so pulling on the head doesn't stress solder joints
- Consider a small multi-pin connector at the neck so the head can be fully detached for maintenance — a JST-XH or Molex connector with enough pins for speaker + LED, plus USB pass-through

### Connector strategy (recommended)

For clean head removal during development:

- **USB cables:** Use short USB extension cables with the socket end glued at the neck opening inside the body; head-side USB plugs simply unplug
- **Speaker + LED wires:** Use a single 4-pin JST-XH connector at the neck (2 pins speaker, 2 pins LED)
- This means head can be fully detached by unplugging 2 USB + 1 JST connector

## Physical Measurements Checklist

Before starting assembly, measure and record these on the physical robot:

- [ ] Head dome interior diameter at widest point (mm)
- [ ] Head dome interior height, neck opening to top (mm)
- [ ] Neck opening diameter (mm)
- [ ] Eye lens socket inner diameter (mm)
- [ ] Eye lens socket depth (mm)
- [ ] Distance between eye socket centers (mm)
- [ ] Existing speaker diameter and mounting details
- [ ] Speaker impedance (multimeter)
- [ ] Visor hinge clearance when flipped up (mm)
- [ ] Top plate vent grille dimensions (mm)
- [ ] Wall thickness of dome plastic (mm, for drilling reference)

## Design Decisions Log

| Decision | Choice | Why |
|----------|--------|-----|
| Camera position | Behind left eye lens (viewer's right) | Natural eye-level POV, reuses existing transparent lens |
| Mic position | Top of head cavity near vent grilles | Maximizes distance from motors, grilles allow sound in |
| Speaker | Reuse original | Saves work, preserves vintage look, sound ports already designed in |
| LED eye | Keep at least one | Iconic look, easy to implement, useful for status indication |
| Projector | Deferred to v2.0 | Adds complexity; route cables with future capacity |
| Head detach | Connector at neck | Essential for development; 2x USB + 1x JST-XH |
