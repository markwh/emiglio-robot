# Head Wiring Guide

## Overview

This document covers the electrical connections between head-mounted components and the Pi + amplifier board in the body. For component placement and mounting, see [head-components.md](../mounting/head-components.md). For circuit design details (resistor values, pin assignments), see the electronics workstream (`develop-electronics`).

## Wiring Diagram

```
┌─────────────────────── HEAD ───────────────────────────┐
│                                                         │
│  USB Webcam ──USB─┐   USB Mic ──USB─┐                  │
│                   │                 │                   │
│  Speaker ──wire───┤   4x LEDs ─────┤                   │
│  (existing)  ┌────┘  (5-wire) ┌────┘                   │
│              │                │                         │
│  3.5mm jack ─┘                │                         │
│  (right eye hole)             │                         │
└──────────────┬────────────────┼────────────────────────┘
               │                │
      ● 3.5mm plug ●   ● JST-XH 6-pin ●  ● USB sockets ● ← NECK
       (speaker)         (4 LEDs+GND)      (cam + mic)
               │                │                │
┌──────────────┼────────────────┼────────────────┼───────┐
│              │                │                │ BODY   │
│   ┌──────────┘    ┌──────────┘    ┌───────────┘        │
│   │               │               │                    │
│   │          4x GPIO pins    USB cam ──→ Pi USB        │
│   │          + shared GND    USB mic ──→ Pi USB        │
│   │                                                    │
│   PAM8403 OUT                                          │
│   (amplified audio)                                    │
│        │                                               │
│   PAM8403 IN                                           │
│        │                                               │
│   Pi 3.5mm audio out                                   │
│                                                        │
└────────────────────────────────────────────────────────┘
```

## Connection Details

### USB Camera → Pi

| Parameter | Value |
|-----------|-------|
| Cable | USB 2.0 Type-A (or stripped to bare wires if space is tight) |
| Length | ~300 mm (12") — head interior to Pi USB port, with slack |
| Pi port | Any USB 2.0/3.0 port (configured as `EMIGLIO_CAMERA_INDEX=0`) |
| Software | OpenCV VideoCapture, 640x480 default |

**Notes:**
- Use the thinnest USB cable available to minimize bulk through the neck
- If using a bare board camera (like an ArduCam or similar), the cable may be a ribbon/FPC — check compatibility with USB
- Test with `uv run python scripts/camera_test.py` once connected

### USB Microphone → Pi

| Parameter | Value |
|-----------|-------|
| Cable | USB 2.0, thin cable |
| Length | ~300 mm (12") |
| Pi port | Any USB 2.0/3.0 port |
| Software | sounddevice library, 16kHz mono (optimized for Whisper STT) |

**Notes:**
- A small USB mic dongle is simplest — just a USB plug with a tiny MEMS mic
- Could also use an I2S MEMS mic (like INMP441) wired directly to Pi GPIO — saves a USB port but requires soldering and config
- Test with `uv run python scripts/audio_test.py` once connected

### Speaker → PAM8403 → Pi

The audio signal chain:

```
Pi audio out → PAM8403 input → PAM8403 amplified output → Speaker
```

| Segment | Cable | Notes |
|---------|-------|-------|
| Pi → PAM8403 input | 3.5mm aux cable or direct solder | Analog audio from Pi headphone jack |
| PAM8403 → 3.5mm plug | 2-conductor, ~22 AWG | Short cable to 3.5mm male plug |

**PAM8403 details:**
- Input: Stereo 3.5mm or bare wire from Pi audio out
- Output: 2x 3W channels (we use one channel, mono)
- Power: 5V from Pi's 5V pin or USB power
- The PAM8403 board lives in the **body** (near the Pi), not in the head

**Speaker audio at neck:**
- 3.5mm female jack mounted in the back of the right eye hole
- PAM8403 L-OUT connects via a short 3.5mm male plug from body
- Tip = speaker +, sleeve = speaker -
- Separate from LED connector for clean cable management

### LEDs → Pi GPIO (4x 5mm red)

| LED | GPIO (BCM) | Physical Pin | Location |
|-----|-----------|-------------|----------|
| Right eye | 24 | 18 | Right eye socket |
| Left eye | 25 | 22 | Left eye socket |
| Right panel | 5 | 29 | Right head panel (behind blue panel) |
| Left panel | 6 | 31 | Left head panel (behind red panel) |

Each LED: 220Ω resistor in series, ~6 mA per LED, ~24 mA total.

**LED wires at neck connector:**
- JST-XH 6-pin connector (pins 1-4: LED signals, pin 5: shared GND, pin 6: spare)
- All 4 LEDs share a single ground return wire

**Resistor placement:** Solder the current-limiting resistor at the LED end (in the head) so the connector carries only logic-level signals. This makes it safe to disconnect without risk of shorting a powered LED.

## Neck Connector Pinout

### 3.5mm Audio Jack (speaker)

Mounted in the back of the right eye hole.

| Contact | Signal |
|---------|--------|
| Tip | Speaker + (PAM8403 L-OUT+) |
| Sleeve | Speaker - (PAM8403 L-OUT-) |

### JST-XH 6-pin (LEDs)

| Pin | Signal | Color suggestion |
|-----|--------|-----------------|
| 1 | Right eye LED (GPIO 24) | White |
| 2 | Left eye LED (GPIO 25) | Yellow |
| 3 | Right panel LED (GPIO 5) | Blue |
| 4 | Left panel LED (GPIO 6) | Green |
| 5 | LED ground (shared) | Black |
| 6 | (spare) | — |

### USB pass-through

Two USB extension socket → plug pairs:
- Socket (female) end hot-glued inside the body barrel, just below neck rim
- Plug (male) end on the head-side cables
- Labeled: `CAM` and `MIC`

## Assembly Sequence

1. **Test components on the bench first** — connect camera, mic, and speaker to Pi outside the robot. Run the test scripts to verify everything works.

2. **Prepare head-side wiring:**
   - Wire speaker to 3.5mm female jack (mount in right eye hole)
   - Solder 4x LED + resistor assemblies
   - Crimp/solder JST-XH 6-pin female connector on LED wires
   - Attach USB cables to camera and mic modules

3. **Prepare body-side wiring:**
   - Solder JST-XH 6-pin male connector to matching wires
   - Solder 3.5mm male plug to PAM8403 output wires
   - Route LED wires to breadboard / Pi GPIO
   - Mount USB extension sockets near neck rim

4. **Route cables through neck:**
   - Feed head-side cables down through neck opening
   - Apply strain relief (zip tie anchor or hot glue saddle)
   - Leave ~50 mm slack in head for serviceability

5. **Connect and test:**
   - Plug in USB, JST, and 3.5mm connectors
   - Place head on body
   - Run test scripts to verify all I/O

6. **Secure head:**
   - Reuse original screw holes if possible
   - Or use a friction fit with felt pads for easy removal during development

## Dependency on Electronics Workstream

The following details are owned by `develop-electronics` and should be finalized there before committing to wiring:

- [x] LED GPIO pin assignments — BCM 24, 25, 5, 6
- [x] PAM8403 power source — Pi 5V pin
- [x] Audio output method — Pi 3.5mm jack → PAM8403 → 3.5mm neck connector
- [x] Microphone type — USB mic dongle
- [x] Full circuit schematic with component values
