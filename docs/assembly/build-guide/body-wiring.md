# Body Wiring Guide

## Overview

The body barrel is where all wiring converges. The Raspberry Pi lives here, along with the breadboard, PAM8403 amplifier, and power input. This document covers how everything connects inside the body, tying together the head cables from above and the base cables from below.

For component placement see [body-barrel.md](../mounting/body-barrel.md). For head-side and base-side wiring details see [head-wiring.md](head-wiring.md) and [base-wiring.md](base-wiring.md).

## Master Wiring Diagram

```
═══════════════════════════════════════════════════════
                    FROM HEAD (above)
═══════════════════════════════════════════════════════
    USB (camera) ──────────────→ Pi USB port 1
    USB (mic) ─────────────────→ Pi USB port 2
    JST-XH pin 1 (speaker +) ─→ breadboard → PAM8403 OUT+
    JST-XH pin 2 (speaker -) ─→ breadboard → PAM8403 OUT-
    JST-XH pin 3 (LED signal) ─→ breadboard → Pi GPIO (TBD)
    JST-XH pin 4 (LED ground) ─→ breadboard → Pi GND rail

═══════════════════════════════════════════════════════
                   PI 5 CONNECTIONS
═══════════════════════════════════════════════════════
    USB-C power port ←───────── wall adapter (5V 3A+)
    USB port 1 ←───────────── camera
    USB port 2 ←───────────── microphone
    3.5mm audio jack ────────→ PAM8403 input
    GPIO header:
      BCM 17 ──→ base connector → TB6612FNG AIN1
      BCM 27 ──→ base connector → TB6612FNG AIN2
      BCM 12 ──→ base connector → TB6612FNG PWMA
      BCM 22 ──→ base connector → TB6612FNG BIN1
      BCM 23 ──→ base connector → TB6612FNG BIN2
      BCM 13 ──→ base connector → TB6612FNG PWMB
      BCM TBD ─→ breadboard → head LED (via JST pin 3)
      3.3V ────→ base connector → TB6612FNG VCC + STBY
      GND ─────→ base connector → TB6612FNG GND
      GND ─────→ breadboard GND rail (head LED, PAM8403)

═══════════════════════════════════════════════════════
                   FROM BASE (below)
═══════════════════════════════════════════════════════
    Screw terminal 1 → AIN1  → Pi GPIO 17
    Screw terminal 2 → AIN2  → Pi GPIO 27
    Screw terminal 3 → PWMA  → Pi GPIO 12
    Screw terminal 4 → BIN1  → Pi GPIO 22
    Screw terminal 5 → BIN2  → Pi GPIO 23
    Screw terminal 6 → PWMB  → Pi GPIO 13
    Screw terminal 7 → VCC   → Pi 3.3V
    Screw terminal 8 → GND   → Pi GND
```

## Pi 5 GPIO Allocation Summary

### Used pins

| BCM Pin | Physical Pin | Function | Destination |
|---------|-------------|----------|-------------|
| 17 | 11 | Motor L forward | TB6612FNG AIN1 (base) |
| 27 | 13 | Motor L backward | TB6612FNG AIN2 (base) |
| 12 | 32 | Motor L PWM | TB6612FNG PWMA (base) |
| 22 | 15 | Motor R forward | TB6612FNG BIN1 (base) |
| 23 | 16 | Motor R backward | TB6612FNG BIN2 (base) |
| 13 | 33 | Motor R PWM | TB6612FNG PWMB (base) |
| TBD | TBD | LED eye | Head JST pin 3 |

### Power pins used

| Pin | Physical Pin | Function |
|-----|-------------|----------|
| 3.3V | 1 or 17 | TB6612FNG VCC + STBY |
| 5V | 2 or 4 | PAM8403 power (if not USB-powered) |
| GND | 6, 9, 14, etc. | Common ground (base + head + PAM8403) |

### Available for future use

| BCM Pins | Notes |
|----------|-------|
| 2, 3 | I2C (SDA, SCL) — for sensors, OLED display, etc. |
| 14, 15 | UART — for serial peripherals |
| 4, 5, 6, 16, 18-21, 24-27 | General GPIO — head swivel servo, additional LEDs, buttons |
| 10, 11, 8, 7 | SPI — for LED strips (NeoPixels), display, etc. |

## Audio Signal Chain

```
Pi 5 audio out ──→ PAM8403 input ──→ PAM8403 output ──→ speaker (in head)
  (3.5mm jack)      (line level)     (amplified, up       (via JST neck
                                      to 3W per ch)        connector)
```

### PAM8403 Wiring

| PAM8403 Pin | Connects To | Notes |
|-------------|-------------|-------|
| VCC (5V) | Pi 5V pin or USB power rail | Powers the amplifier |
| GND | Pi GND (breadboard rail) | Common ground |
| L-IN / R-IN | Pi 3.5mm audio jack (tip = L, ring = R) | Use either channel for mono speaker |
| L-OUT+ / L-OUT- | Breadboard → JST neck connector pins 1-2 | Amplified audio to head speaker |

**Wiring notes:**
- Use a short 3.5mm aux cable from Pi to PAM8403 input, or solder directly
- Only one channel (L or R) is needed for the single mono speaker
- The PAM8403 has a small potentiometer for volume — set it during testing

### Audio output alternatives

| Method | Pros | Cons |
|--------|------|------|
| **3.5mm jack (recommended for v1.0)** | Simplest, no config needed, analog out works out of box | Lower audio quality (PWM-based on Pi) |
| I2S DAC (e.g., MAX98357A) | Better audio quality, digital path | Requires soldering, config, uses GPIO pins |
| USB DAC | Good quality, plug-and-play | Uses a USB port, adds bulk |

**Recommendation:** Start with 3.5mm for v1.0. Upgrade to I2S DAC if audio quality matters for v2.0.

## Power Distribution

```
    Wall adapter (USB-C, 5V 3A+)
         │
         ▼
    Pi 5 USB-C power input
         │
         ├──→ Pi 5 (runs from its own PSU)
         │
         ├──→ 5V pin on GPIO header
         │        │
         │        ├──→ PAM8403 VCC (via breadboard)
         │        │
         │        └──→ (available for future 5V peripherals)
         │
         └──→ 3.3V pin on GPIO header
                  │
                  └──→ TB6612FNG VCC + STBY (via base connector)


    4xAA Battery Pack (in base, 6V)
         │
         ├──→ TB6612FNG VM (motor power)
         │
         └──→ GND ──→ common with Pi GND (via base connector)
```

**Key points:**
- Pi and motors have **separate power supplies** — this is intentional
- They share a **common ground** — required for the TB6612FNG to read GPIO logic levels
- The Pi's 5V pin supplies the PAM8403 (~200 mA draw, well within the Pi's capacity)
- The Pi 5 requires a **5V 3A+ USB-C supply** (official Pi power supply recommended)

## Breadboard Layout

Suggested breadboard organization:

```
    ┌──────────────────────────────────────────┐
    │  + ─────────── 5V POWER RAIL ─────────── │
    │  - ─────────── GND RAIL ─────────────── │
    │                                          │
    │  [GPIO jumpers from Pi header]           │
    │  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·          │
    │                                          │
    │  ZONE A: Motor control signals           │
    │  GPIO 17,27,12 → base connector (left)   │
    │  GPIO 22,23,13 → base connector (right)  │
    │  3.3V, GND → base connector              │
    │                                          │
    │  ZONE B: Head interface                  │
    │  GPIO TBD → LED JST pin 3               │
    │  PAM8403 OUT+ → speaker JST pin 1       │
    │  PAM8403 OUT- → speaker JST pin 2       │
    │  GND → LED JST pin 4                    │
    │                                          │
    │  ZONE C: PAM8403                         │
    │  [PAM8403 board pins inserted here]      │
    │  VCC ← 5V rail                           │
    │  GND ← GND rail                          │
    │  L-IN ← Pi 3.5mm (via aux cable)        │
    │                                          │
    │  + ─────────── 5V POWER RAIL ─────────── │
    │  - ─────────── GND RAIL ─────────────── │
    └──────────────────────────────────────────┘
```

## Assembly Sequence

### Phase 1: Canister preparation

1. **Measure barrel interior** — confirm canister dimensions
2. **Source or make the canister** — oatmeal canister, PVC pipe section, or rolled corrugated plastic
3. **Cut cable slots** — one at the top edge (head cables) and one at the bottom edge (base cables)
4. **Test fit** — canister should slide in and out of the barrel freely
5. **Mark mounting positions** — hold Pi and breadboard against canister wall/floor, mark hole positions

### Phase 2: Component mounting

6. **Mount Pi 5** — M2.5 standoffs through canister wall/floor
7. **Attach heat sink** — passive aluminum heat sink on Pi SoC
8. **Stick breadboard** — adhesive backing onto canister surface, near Pi GPIO header
9. **Mount PAM8403** — on breadboard or adjacent to it with foam tape

### Phase 3: Internal wiring

10. **Wire breadboard power rails** — 5V and GND from Pi GPIO header
11. **Wire motor GPIO signals** — Pi GPIO pins → breadboard zone A → base connector wires
12. **Wire 3.3V + GND to base connector** — for TB6612FNG logic power
13. **Wire PAM8403** — 5V, GND, audio input from Pi 3.5mm jack
14. **Wire head interface** — PAM8403 output to breadboard zone B → head JST connector, LED GPIO to zone B → head JST connector
15. **Connect USB extension sockets** — mount near barrel rim for head camera + mic cables

### Phase 4: Cable routing and test

16. **Dress cables** — route along canister walls, bundle with zip ties
17. **Insert canister into barrel** — feed base connector wires through bottom slot
18. **Plug in power cable** — route USB-C through rear wall hole or top gap
19. **Connect base connector** — plug in screw terminal or multi-pin connector
20. **Connect head** — plug in USB cables and JST connector, place head on barrel
21. **Full system test:**
    ```bash
    EMIGLIO_HARDWARE_MODE=real uv run python -m emiglio
    ```

## Dependency on Other Workstreams

### Electronics (`develop-electronics`)

- [ ] LED GPIO pin assignment
- [ ] PAM8403 power source confirmation (Pi 5V vs. separate)
- [ ] Audio output method confirmation (3.5mm vs. I2S)
- [ ] Decoupling capacitor recommendations for breadboard power rails
- [ ] Full integrated circuit schematic

### Software (`develop-software`)

- [ ] ALSA/PulseAudio configuration for Pi 5 audio output
- [ ] Camera and mic device enumeration (which USB port = which device)
- [ ] systemd service configuration for auto-start (deploy/emiglio.service)
