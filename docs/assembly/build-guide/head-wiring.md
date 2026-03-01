# Head Wiring Guide

## Overview

This document covers the electrical connections between head-mounted components and the Pi + amplifier board in the body. For component placement and mounting, see [head-components.md](../mounting/head-components.md). For circuit design details (resistor values, pin assignments), see the electronics workstream (`develop-electronics`).

## Wiring Diagram

```
┌─────────────────────── HEAD ───────────────────────────┐
│                                                         │
│  USB Webcam ──USB─┐   USB Mic ──USB─┐                  │
│                   │                 │                   │
│  Speaker ──2wire──┤   LED ──2wire───┤                   │
│  (existing)  ┌────┘            ┌────┘                   │
│              │                 │                        │
└──────────────┼─────────────────┼────────────────────────┘
               │                 │
         ● JST-XH 4-pin ●   ● USB sockets ●  ← NECK CONNECTORS
         (speaker + LED)    (cam + mic)
               │                 │
┌──────────────┼─────────────────┼────────────────────────┐
│              │                 │              BODY       │
│              │                 │                         │
│   ┌──────────┘                 └──────────┐              │
│   │ speaker+  speaker-  LED+  LED-        │              │
│   │    │         │       │      │         │              │
│   │    └────┬────┘       │      │     USB cam ──→ Pi USB│
│   │         │            │      │     USB mic ──→ Pi USB│
│   │    PAM8403 OUT       │      │                       │
│   │    (amplified        GPIO pin                       │
│   │     audio)           (BCM TBD)                      │
│   │         │                                           │
│   │    PAM8403 IN                                       │
│   │         │                                           │
│   │    Pi 3.5mm / I2S / USB audio out                   │
│   │                                                     │
└───┼─────────────────────────────────────────────────────┘
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
| PAM8403 → Speaker | 2-conductor, ~22 AWG | Runs through neck to head |

**PAM8403 details:**
- Input: Stereo 3.5mm or bare wire from Pi audio out
- Output: 2x 3W channels (we use one channel, mono)
- Power: 5V from Pi's 5V pin or USB power
- The PAM8403 board lives in the **body** (near the Pi), not in the head
- Only the amplified speaker wires go up through the neck

**Speaker wire at neck connector:**
- 2 pins on the JST-XH 4-pin connector (pins 1-2)
- Polarity matters — mark + and - on both sides

### LED Eye → Pi GPIO

| Parameter | Value |
|-----------|-------|
| LED type | Standard 5mm red LED (or RGB/NeoPixel for status colors) |
| Resistor | 220Ω–330Ω in series (for 3.3V GPIO → standard red LED) |
| GPIO pin | TBD — to be assigned by electronics workstream |
| Cable | 2-conductor, ~26 AWG (thin signal wire) |

**LED wire at neck connector:**
- 2 pins on the JST-XH 4-pin connector (pins 3-4)
- Pin 3: GPIO signal (through resistor, which can be soldered at either end)
- Pin 4: Ground

**Resistor placement:** Solder the current-limiting resistor at the LED end (in the head) so the neck connector carries only logic-level signals. This makes it safe to disconnect without risk of shorting a powered LED.

## Neck Connector Pinout

### JST-XH 4-pin (speaker + LED)

| Pin | Signal | Color suggestion |
|-----|--------|-----------------|
| 1 | Speaker + | Red |
| 2 | Speaker - | Black |
| 3 | LED signal (through resistor) | White |
| 4 | LED ground | Green |

### USB pass-through

Two USB extension socket → plug pairs:
- Socket (female) end hot-glued inside the body barrel, just below neck rim
- Plug (male) end on the head-side cables
- Labeled: `CAM` and `MIC`

## Assembly Sequence

1. **Test components on the bench first** — connect camera, mic, and speaker to Pi outside the robot. Run the test scripts to verify everything works.

2. **Prepare head-side wiring:**
   - Solder speaker wires to existing speaker (or replacement)
   - Solder LED + resistor
   - Crimp/solder JST-XH female connector on speaker + LED wires
   - Attach USB cables to camera and mic modules

3. **Prepare body-side wiring:**
   - Solder JST-XH male connector to matching wires
   - Route speaker wires to PAM8403 output terminals
   - Route LED wires to breadboard / Pi GPIO
   - Mount USB extension sockets near neck rim

4. **Route cables through neck:**
   - Feed head-side cables down through neck opening
   - Apply strain relief (zip tie anchor or hot glue saddle)
   - Leave ~50 mm slack in head for serviceability

5. **Connect and test:**
   - Plug in USB and JST connectors
   - Place head on body
   - Run test scripts to verify all I/O

6. **Secure head:**
   - Reuse original screw holes if possible
   - Or use a friction fit with felt pads for easy removal during development

## Dependency on Electronics Workstream

The following details are owned by `develop-electronics` and should be finalized there before committing to wiring:

- [ ] LED GPIO pin assignment (BCM number)
- [ ] PAM8403 power source (Pi 5V pin vs. separate regulator)
- [ ] Audio output method from Pi (3.5mm jack vs. I2S vs. USB DAC)
- [ ] Whether to use USB mic or I2S mic (affects cable count through neck)
- [ ] Full circuit schematic with component values
