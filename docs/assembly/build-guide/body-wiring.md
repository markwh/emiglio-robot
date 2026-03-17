# Body Wiring Guide

## Overview

The body barrel is where all wiring converges. The Raspberry Pi lives here, along with the breadboard, PAM8403 amplifier, and power input. This document covers how everything connects inside the body, tying together the head cables from above and the base cables from below.

For component placement see [body-barrel.md](../mounting/body-barrel.md). For head-side and base-side wiring details see [head-wiring.md](head-wiring.md) and [base-wiring.md](base-wiring.md).

## Master Wiring Diagram

```
═══════════════════════════════════════════════════════
              FROM HEAD (above) — via box top
═══════════════════════════════════════════════════════
    USB (camera) ──────────────→ Pi USB port
    USB (mic) ─────────────────→ Pi USB port
    JST-XH 6-pin (LEDs):
      Pin 1 (right eye)  ─────→ panel → breadboard → Pi GPIO 24
      Pin 2 (left eye)   ─────→ panel → breadboard → Pi GPIO 25
      Pin 3 (right panel) ────→ panel → breadboard → Pi GPIO 5
      Pin 4 (left panel)  ────→ panel → breadboard → Pi GPIO 6
      Pin 5 (LED GND)    ─────→ panel → breadboard GND rail
      Pin 6 (spare)       ────→ —
    3.5mm OUT jack ────────────→ head speaker (via neck cable)

═══════════════════════════════════════════════════════
              PI 5 CONNECTIONS (inside box)
═══════════════════════════════════════════════════════
    USB-C power port ←───────── wall adapter (5V 3A+)
    USB port ←─────────────── camera (from head)
    USB port ←─────────────── microphone (from head)
    USB port ──────────────→ USB-to-3.5mm adapter (outside box)
                                    │
                              short aux cable
                                    │
                              3.5mm IN jack (Face A) → PAM8403 input
    GPIO header:
      BCM 17 ──→ panel → JST-XH 5p "L" pin 1 → TB6612FNG AIN1
      BCM 27 ──→ panel → JST-XH 5p "L" pin 2 → TB6612FNG AIN2
      BCM 12 ──→ panel → JST-XH 5p "L" pin 3 → TB6612FNG PWMA
      BCM 22 ──→ panel → JST-XH 5p "R" pin 1 → TB6612FNG BIN1
      BCM 23 ──→ panel → JST-XH 5p "R" pin 2 → TB6612FNG BIN2
      BCM 13 ──→ panel → JST-XH 5p "R" pin 3 → TB6612FNG PWMB
      BCM 24 ──→ panel → JST-XH 6p pin 1 → right eye LED
      BCM 25 ──→ panel → JST-XH 6p pin 2 → left eye LED
      BCM 5  ──→ panel → JST-XH 6p pin 3 → right panel LED
      BCM 6  ──→ panel → JST-XH 6p pin 4 → left panel LED
      3.3V ────→ panel → JST-XH 5p "L"+"R" pin 4 → TB6612FNG VCC+STBY
      5V ──────→ breadboard → PAM8403 VCC
      GND ─────→ panel → JST-XH 5p "L"+"R" pin 5 → TB6612FNG GND
      GND ─────→ breadboard GND rail (LEDs, PAM8403)

═══════════════════════════════════════════════════════
              FROM BASE (below) — via box output face
═══════════════════════════════════════════════════════
    JST-XH 5-pin "L":
      Pin 1 → AIN1  → Pi GPIO 17
      Pin 2 → AIN2  → Pi GPIO 27
      Pin 3 → PWMA  → Pi GPIO 12
      Pin 4 → VCC   → Pi 3.3V
      Pin 5 → GND   → Pi GND
    JST-XH 5-pin "R":
      Pin 1 → BIN1  → Pi GPIO 22
      Pin 2 → BIN2  → Pi GPIO 23
      Pin 3 → PWMB  → Pi GPIO 13
      Pin 4 → VCC   → Pi 3.3V
      Pin 5 → GND   → Pi GND
```

All JST-XH and 3.5mm connectors are mounted on the box via a perfboard connector panel (Face B) and panel-mount jacks. See [connector-panel.md](connector-panel.md) for build details.

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
| 24 | 18 | Right eye LED | Head JST-XH 6p pin 1 |
| 25 | 22 | Left eye LED | Head JST-XH 6p pin 2 |
| 5 | 29 | Right panel LED | Head JST-XH 6p pin 3 |
| 6 | 31 | Left panel LED | Head JST-XH 6p pin 4 |

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
| 4, 16, 18-21, 26, 27 | General GPIO — head swivel servo, additional LEDs, buttons |
| 10, 11, 8, 7 | SPI — for LED strips (NeoPixels), display, etc. |

## Audio Signal Chain

The Pi 5 has no built-in 3.5mm jack, so audio output uses a USB-to-3.5mm adapter. The adapter doesn't fit inside the electronics box, so the signal exits the box as USB, gets converted externally, and re-enters the box as analog for amplification.

```
Pi USB ──→ USB-to-3.5mm adapter ──→ 3.5mm IN jack ──→ PAM8403 ──→ 3.5mm OUT jack ──→ speaker
(inside     (outside box,             (Face A,          (breadboard,   (Face B,         (in head,
 box)        short aux cable)          into box)          inside box)    out of box)      via neck)
```

### PAM8403 Wiring

| PAM8403 Pin | Connects To | Notes |
|-------------|-------------|-------|
| VCC (5V) | Pi 5V pin (breadboard rail) | Powers the amplifier |
| GND | Pi GND (breadboard rail) | Common ground |
| L-IN | 3.5mm IN jack tip (Face A, via breadboard) | Line-level audio from USB adapter |
| GND | 3.5mm IN jack sleeve (Face A, via breadboard) | Audio ground |
| L-OUT+ | 3.5mm OUT jack tip (Face B, via breadboard) | Amplified audio to speaker |
| L-OUT- | 3.5mm OUT jack sleeve (Face B, via breadboard) | Amplified audio return |

**Wiring notes:**
- The USB adapter plugs into a Pi USB port and hangs outside the box
- A short aux cable connects the adapter's 3.5mm output to the IN jack on Face A
- Only one channel (L) is needed for the single mono speaker
- The PAM8403 has a small potentiometer for volume — set it during testing
- See [connector-panel.md](connector-panel.md) for jack mounting details

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


    4xD Battery Pack (in base, 6V)
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

Suggested breadboard organization. All JST-XH and 3.5mm connections route through the connector panel (see [connector-panel.md](connector-panel.md)) — the breadboard connects to the panel's internal wires, not directly to external cables.

```
    ┌──────────────────────────────────────────┐
    │  + ─────────── 5V POWER RAIL ─────────── │
    │  - ─────────── GND RAIL ───────────────  │
    │                                          │
    │  [GPIO jumpers from Pi header]           │
    │  ·  ·  ·  ·  ·  ·  ·  ·  ·  ·          │
    │                                          │
    │  ZONE A: Motor control signals           │
    │  GPIO 17,27,12 → panel → JST 5p "L"     │
    │  GPIO 22,23,13 → panel → JST 5p "R"     │
    │  3.3V, GND → panel → JST 5p "L"+"R"     │
    │                                          │
    │  ZONE B: LED signals                     │
    │  GPIO 24,25,5,6 → panel → JST 6p        │
    │  GND → panel GND bus                     │
    │                                          │
    │  ZONE C: PAM8403                         │
    │  [PAM8403 board pins inserted here]      │
    │  VCC ← 5V rail                           │
    │  GND ← GND rail                         │
    │  L-IN ← 3.5mm IN jack (Face A)          │
    │  L-OUT+ → 3.5mm OUT jack (Face B)       │
    │  L-OUT- → 3.5mm OUT jack (Face B)       │
    │                                          │
    │  + ─────────── 5V POWER RAIL ─────────── │
    │  - ─────────── GND RAIL ───────────────  │
    └──────────────────────────────────────────┘
```

## Assembly Sequence

### Phase 1: Box preparation

1. **Cut holes in webcam box** — see [connector-panel.md](connector-panel.md) for Face A and Face B layouts
2. **Cut ventilation holes** — several ~15mm holes near the Pi SoC location
3. **Test fit** — box should slide in and out of the barrel freely

### Phase 2: Component mounting

4. **Mount Pi 5** — M2.5 standoffs against box left wall (ports facing Face A)
5. **Attach heat sink** — passive aluminum heat sink on Pi SoC
6. **Stick breadboard** — adhesive backing flat on box bottom, near Pi GPIO header

### Phase 3: Connector panel

7. **Build and install connector panel** — follow [connector-panel.md](connector-panel.md) steps 1-10
8. **Mount 3.5mm jacks** — audio IN on Face A, audio OUT on Face B (connector-panel.md steps 11-14)
9. **Mount PAM8403** — on breadboard or adjacent to it with foam tape

### Phase 4: Internal wiring

10. **Wire breadboard power rails** — 5V and GND from Pi GPIO header
11. **Wire motor GPIO signals** — Pi GPIO pins → breadboard zone A → panel wires → JST-XH 5p "L"+"R"
12. **Wire 3.3V + GND to panel** — for TB6612FNG logic power via JST-XH connectors
13. **Wire LED GPIO signals** — Pi GPIO 24, 25, 5, 6 → breadboard zone B → panel wires → JST-XH 6p
14. **Wire PAM8403** — 5V, GND, L-IN from 3.5mm IN jack, L-OUT to 3.5mm OUT jack

### Phase 5: Cable routing and test

15. **Dress cables** — route along box walls, bundle with zip ties
16. **Insert box into barrel** — slide in from the top
17. **Plug in power cable** — USB-C through Face A
18. **Plug in USB adapter** — into Pi USB port, short aux cable to 3.5mm IN jack
19. **Connect base harnesses** — plug JST-XH 5p "L" and "R" into Face B
20. **Connect head harnesses** — plug JST-XH 6p (LEDs) into Face B, 3.5mm cable into OUT jack, USB camera + mic into Pi ports
21. **Full system test:**
    ```bash
    EMIGLIO_HARDWARE_MODE=real uv run python -m emiglio
    ```

## Dependency on Other Workstreams

### Electronics (`develop-electronics`)

- [x] LED GPIO pin assignment — BCM 24, 25, 5, 6
- [x] PAM8403 power source — Pi 5V pin
- [x] Audio output method — USB adapter → 3.5mm IN jack → PAM8403 → 3.5mm OUT jack
- [ ] Decoupling capacitor recommendations for breadboard power rails
- [ ] Full integrated circuit schematic

### Software (`develop-software`)

- [ ] ALSA/PulseAudio configuration for Pi 5 audio output
- [ ] Camera and mic device enumeration (which USB port = which device)
- [ ] systemd service configuration for auto-start (deploy/emiglio.service)
