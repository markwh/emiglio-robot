# Body Barrel Mounting Plan

## Overview

The body barrel is the white cylindrical section between the locomotion base and the head dome. It's the robot's central hub — housing the Raspberry Pi, breadboard, PAM8403 amplifier, and power input, while routing cables between the head above and the base below.

The barrel is an open-top cylinder with arm sockets on both sides. Its interior is spacious enough to fit a Pi 5 and supporting electronics, especially with the oatmeal canister compartment idea from the original design vision.

### Reference Frames

| Frame | What it shows |
|-------|---------------|
| `frame_0020.jpg` | Body without head, side view — open barrel rim, arm socket, interior visible |
| `frame_0025.jpg` | Body without head, front view — barrel sitting on base, GP Toys sticker |
| `frame_0035.jpg` | Body close-up — decorative panels, seam line, lower edge on base |
| `frame_0050.jpg` | Body with Chromebox next to it — scale reference for electronics |
| `frame_0055.jpg` | Body front, clean shot |
| `frame_0004.jpg` | Full robot assembled — body between base and head |

## Body Anatomy

### Cross-section (front view)

```
              ┌───── head sits here ─────┐
              │                          │
         ┌────┴──────────────────────────┴────┐
         │         open barrel rim             │
         │    ┌────────────────────────┐       │
    arm ─┤    │                        │       ├─ arm
  socket │    │    INTERIOR CAVITY     │       │ socket
         │    │                        │       │
         │    │   (Pi, breadboard,     │       │
         │    │    PAM8403, wiring)    │       │
         │    │                        │       │
         │    └────────────────────────┘       │
         │         barrel floor / base seat    │
         └─────────────────────────────────────┘
                   sits on base platform
```

### Top-down view (looking into barrel)

```
              ┌──────────────────────┐
             ╱                        ╲
            │     BARREL INTERIOR      │
            │                          │
    arm ────┤                          ├──── arm
    socket  │                          │     socket
            │                          │
             ╲                        ╱
              └──────────────────────┘

    Interior is roughly cylindrical.
    Arm sockets protrude on left and right sides.
```

### Key features

- **Open top rim** — the head dome sits on this rim and is secured with screws (or friction fit during dev)
- **Cylindrical interior** — spacious, smooth walls, suitable for mounting electronics
- **Arm sockets** — protrude from left and right sides; one arm currently attached, one missing. These are structural features of the shell — they reduce the usable diameter slightly at the socket level
- **Barrel floor** — sits directly on the base platform. May have existing holes or mounting features from the original toy's internal circuit board
- **Seam line** — the barrel shell is formed from two halves joined at a vertical seam. Can be separated for access if needed, but ideally electronics are accessible from the top
- **Decorative panels/stickers** — front has a circular grille sticker feature. These are cosmetic only but contribute to the vintage aesthetic

## Electronics Enclosure: Webcam Box

**Concept:** A small cardboard box (the box the USB webcam arrived in) serves as a removable electronics module inside the barrel. The Pi 5 and half-size breadboard mount against different interior surfaces of the box, with all connections made inside. Holes cut in the box provide cable pass-through, airflow, and access.

**Advantages:**
- Electronics are fully accessible without disassembling the robot — pull the box out to service
- Protects vintage plastic shell from hot glue / drilling / permanent modification
- Can be pre-wired and tested outside the robot
- Rigid mounting surface for the Pi and breadboard
- Rectangular box fits the rectangular components better than a cylindrical canister

**Implementation:**

```
    Head (removed)
         ↓
    ┌─────────────────────┐  ← barrel rim
    │  ┌───────────────┐  │
    │  │  webcam box   │  │  ← removable electronics module
    │  │               │  │
    │  │  Pi 5 (wall)  │  │
    │  │  breadboard   │  │
    │  │  (other wall) │  │
    │  │               │  │
    │  │  holes for:   │  │
    │  │  - cables ────┼──┼──→ to base / head connectors
    │  │  - ventilation│  │
    │  └───────────────┘  │
    └─────────────────────┘  ← barrel floor
```

**Holes to cut in box:**
- **Top edge:** JST-XH 6-pin (head LEDs), 3.5mm audio (speaker), 2x USB (camera + mic)
- **Bottom edge:** 2x JST-XH 5-pin (base motor harnesses)
- **Rear/side:** USB-C power cable entry
- **Ventilation:** Several ~15mm holes or a slot grid near the Pi SoC to prevent heat buildup

## Components to Mount

### 1. Raspberry Pi 5 (4GB)

**Position:** Inside the canister/sled, mounted to its wall or floor.

**Why in the body:** Central location with cable access to both head (USB ports facing up) and base (GPIO header facing down). The body has the most space for the Pi and its heat sink.

**Mounting approach:**
- Mount Pi to canister wall using M2.5 standoffs (Pi has 4 mounting holes)
- Orient so USB/Ethernet ports face upward (toward head cables)
- GPIO header should be accessible for the base-to-body jumper wires
- If using canister: screw standoffs through the canister wall into the Pi

**Thermal considerations:**
- The Pi 5 runs warm under load — needs airflow or a passive heat sink
- The barrel is enclosed, so heat will build up
- **Minimum:** Attach a passive aluminum heat sink to the Pi's SoC
- **Better:** Drill small ventilation holes in the barrel wall (rear, hidden from front view) or rely on the open top when the head is friction-fit (not sealed)
- The canister approach helps — pulling it out lets the Pi cool during extended bench work

**Orientation options:**

```
Option A: Pi horizontal               Option B: Pi vertical
(flat on canister floor)               (mounted to canister wall)

┌──────────────┐                      ┌──────────────┐
│  ┌────────┐  │                      │  │Pi│         │
│  │  Pi 5  │  │                      │  │  │ bread-  │
│  └────────┘  │                      │  │  │ board   │
│  ┌────────┐  │                      │  │  │         │
│  │ bread- │  │                      │  └──┘         │
│  │ board  │  │                      │               │
│  └────────┘  │                      └───────────────┘
└──────────────┘

A is simpler; B saves vertical space
Recommend A for prototyping
```

### 2. Half-Size Breadboard

**Position:** Inside the canister, next to or stacked above the Pi.

**Why:** Central prototyping hub for connecting GPIO wires from the base connector, head connector wires (speaker, LED), and the PAM8403 amplifier. Avoids permanent soldering during development.

**Mounting approach:**
- Breadboards usually have adhesive backing — stick directly to canister floor or wall
- Position close to Pi GPIO header to keep jumper wires short
- Leave room for fingers to insert/remove jumper wires

### 3. PAM8403 Amplifier Board

**Position:** On the breadboard, or mounted beside it inside the canister.

**What it does:** Amplifies the Pi's audio output to drive the speaker in the head. Input is line-level from Pi (3.5mm jack or I2S); output is amplified analog to speaker.

**Mounting approach:**
- Tiny board (~20x20 mm) — can be soldered to a small piece of perfboard or friction-fit on the breadboard
- Position near the top of the canister so speaker output wires have a short path to the head cable exit

**Connections:**
- Input: Pi audio out (3.5mm or I2S — see body wiring guide)
- Output: 2-wire speaker cable routed up to the head neck connector
- Power: 5V from Pi or USB power rail

### 4. Power Input

**Position:** A USB-C power cable entering the body from the rear.

**Why:** For v1.0 the robot is wall-powered (USB-C power supply for the Pi). The power cable needs to enter the body and reach the Pi's USB-C port.

**Mounting approach:**
- Drill or cut a small hole (~10 mm) in the rear of the barrel wall for the USB-C cable to pass through
- Use a rubber grommet to protect the cable and add strain relief
- Route the cable to the Pi's USB-C power port
- **This is the one permanent modification to the barrel shell** — choose a discrete location on the rear

**Alternative (no drilling):** Route the power cable through the barrel top, between the head and the barrel rim. This avoids modifying the shell but means the cable is visible and the head can't fully seat.

**Future (v2.0+):** Replace wall power with a battery pack (LiPo or USB power bank) mounted inside the canister. This eliminates the need for the cable pass-through entirely.

### 5. WiFi Antenna (Pi 5 built-in)

**No mounting needed.** The Pi 5 has built-in WiFi. The plastic barrel shell is RF-transparent, so no external antenna is required. If signal strength is an issue, the open top provides additional RF path.

## Cable Interfaces

The body is the junction point. Cables arrive from two directions:

### From above (head)

Through the box top / barrel rim / neck opening:
- 2x USB cables (camera, mic)
- 1x JST-XH 6-pin (4 LED signals + shared GND + spare)
- 1x 3.5mm audio plug (speaker from PAM8403)

These plug into:
- USB cables → Pi USB ports
- LED JST wires → Pi GPIO pins 24, 25, 5, 6 (via breadboard)
- 3.5mm plug → 3.5mm jack on head speaker cable

### From below (base)

Through the box bottom / barrel floor:
- 1x JST-XH 5-pin "L" (AIN1, AIN2, PWMA, VCC, GND)
- 1x JST-XH 5-pin "R" (BIN1, BIN2, PWMB, VCC, GND)

These connect to:
- Motor control signals → Pi GPIO header (via breadboard or direct jumper)
- VCC → Pi 3.3V pin (duplicated on both connectors for redundancy)
- GND → Pi GND pin (shared with motor battery GND via base breadboard)

### Power in

Through rear barrel wall (or top gap):
- 1x USB-C cable → Pi power port

### Internal routing layout

```
            HEAD CABLES
               │
    ┌──────────┼──────────────┐
    │  USB ────┼──→ Pi USB    │
    │  JST ────┼──→ breadboard│
    │          │              │
    │    ┌─────┴─────┐        │
    │    │  Pi 5     │        │
    │    │  ┌─GPIO─┐ │        │
    │    └──┼──────┼─┘        │
    │       │      │          │
    │    ┌──┴──────┴──┐       │
    │    │ breadboard  │       │
    │    │ PAM8403     │       │
    │    └──────┬──────┘       │
    │           │              │ ←── USB-C power in (rear)
    │  base ────┘              │
    │  connector               │
    └──────────┼──────────────┘
               │
          BASE CABLES
```

## Physical Measurements Checklist

Before starting assembly, measure and record on the physical body:

### Barrel exterior
- [ ] Barrel outer diameter at widest point (mm)
- [ ] Barrel height, base seat to top rim (mm)
- [ ] Arm socket protrusion width (mm) — reduces usable interior at that level
- [ ] Shell wall thickness (mm) — for drilling reference
- [ ] Location and size of any existing holes in barrel floor (from original wiring)
- [ ] Rear wall area suitable for power cable pass-through

### Barrel interior
- [ ] Interior diameter at widest point (mm) — determines canister size
- [ ] Interior height, floor to rim (mm)
- [ ] Any internal ribs, bosses, or screw posts that reduce usable space
- [ ] Barrel floor: solid or has openings to base?

### Canister sizing
- [ ] Standard oatmeal canister diameter and height vs. interior dimensions
- [ ] Clearance needed at top for head cable routing (~20 mm)
- [ ] Clearance needed at bottom for base cable exit (~15 mm)

### Pi 5 dimensions (for reference)
- Board: 85 x 56 mm
- Height with heat sink: ~15-25 mm depending on heat sink
- Mounting holes: M2.5, 58 x 49 mm pattern
- USB/Ethernet ports on one short edge
- GPIO header on one long edge
- USB-C power on one short edge (same side as HDMI)

## Design Decisions Log

| Decision | Choice | Why |
|----------|--------|-----|
| Pi location | Body barrel (in canister) | Central hub, cable access to head and base, most space |
| Electronics enclosure | Webcam box (cardboard) — removable module | Easy access, no permanent shell modification (except power hole), bench-testable, rectangular shape fits Pi + breadboard well |
| Pi orientation | Horizontal on canister floor | Simplest for prototyping; USB ports face up toward head cables |
| Power input | USB-C through rear wall hole (v1.0) | Simple, one small permanent modification; future battery eliminates it |
| Breadboard | Inside canister, next to Pi | Prototyping flexibility; avoids permanent soldering |
| PAM8403 location | On/near breadboard | Short wire path to both Pi audio out and head speaker cable |
| Ventilation | Passive heat sink + open top gap | Minimal modification; barrel is not sealed with friction-fit head |

## Risks and Considerations

### Space constraints
- The Pi 5 + breadboard + PAM8403 + wiring need to fit in a cylinder. Measure before committing to the canister approach — if the barrel interior is too narrow, components may need to mount directly to the barrel wall instead.

### Cable congestion
- The body is where all cables converge: 2 USB from head, 1 JST from head, ~8 wires from base, plus USB-C power. Plan cable routing carefully to avoid a rat's nest.
- The canister helps here — cables can be dressed along the canister wall before exiting through slots.

### Head removal clearance
- When lifting the head off for service, the USB and JST cables from the head must have enough slack (or be disconnected) to allow separation.
- The neck connector strategy (from head-components.md) handles this — just unplug the connectors.

### Weight and center of gravity
- The Pi, breadboard, and battery (future) add weight to the body.
- Keep heavy components low in the barrel to maintain a low center of gravity.
- The canister should sit on the barrel floor, not suspended from the rim.

### Arm sockets
- The arm sockets reduce the usable diameter at their level. Route the canister past or below them.
- The missing arm's socket could be repurposed as a cable pass-through or ventilation port.
