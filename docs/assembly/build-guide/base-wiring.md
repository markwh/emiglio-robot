# Base Wiring Guide

## Overview

This document covers the electrical connections for the locomotion base: motors to the TB6612FNG driver, the driver to Pi GPIO, and motor battery power. For component placement see [base-locomotion.md](../mounting/base-locomotion.md). For circuit design details see the electronics workstream (`develop-electronics`).

## System Diagram

```
                    BODY (webcam box, Pi lives here)
    ┌──────────────────────────────────────────────────┐
    │                                                  │
    │   Raspberry Pi 5                                 │
    │   ┌──────────────────────┐                       │
    │   │ GPIO 17 (BCM) ──────┼── AIN1 ─┐             │
    │   │ GPIO 27 (BCM) ──────┼── AIN2 ─┤ JST-XH     │
    │   │ GPIO 12 (BCM) ──────┼── PWMA ─┤ 5-pin "L"  │
    │   │ 3.3V ───────────────┼── VCC ──┤             │
    │   │ GND ────────────────┼── GND ──┘             │
    │   │                     │                        │
    │   │ GPIO 22 (BCM) ──────┼── BIN1 ─┐             │
    │   │ GPIO 23 (BCM) ──────┼── BIN2 ─┤ JST-XH     │
    │   │ GPIO 13 (BCM) ──────┼── PWMB ─┤ 5-pin "R"  │
    │   │ 3.3V ───────────────┼── VCC ──┤             │
    │   │ GND ────────────────┼── GND ──┘             │
    │   └──────────────────────┘                       │
    │                                                  │
    └──────────────────────┼───────────────────────────┘
                           │
              ═══ 2x JST-XH 5-pin ═══  (base-to-body interface)
                     "L"       "R"
                           │
    ┌──────────────────────┼───────────────────────────┐
    │                      │                  BASE     │
    │              TB6612FNG Board                     │
    │   ┌──────────────────────────────┐               │
    │   │ VCC ←── 3.3V (logic power)   │               │
    │   │ GND ←── Pi GND               │               │
    │   │ STBY ──── tied to VCC        │               │
    │   │                              │               │
    │   │ AIN1 ←── GPIO 17 (left fwd)  │               │
    │   │ AIN2 ←── GPIO 27 (left bwd)  │               │
    │   │ PWMA ←── GPIO 12 (left PWM)  │               │
    │   │ AO1 ────→ Motor L terminal + │               │
    │   │ AO2 ────→ Motor L terminal - │               │
    │   │                              │               │
    │   │ BIN1 ←── GPIO 22 (right fwd) │               │
    │   │ BIN2 ←── GPIO 23 (right bwd) │               │
    │   │ PWMB ←── GPIO 13 (right PWM) │               │
    │   │ BO1 ────→ Motor R terminal + │               │
    │   │ BO2 ────→ Motor R terminal - │               │
    │   │                              │               │
    │   │ VM ←──── Battery + (6V D cells) │            │
    │   │ GND ←─── Battery - (GND)     │               │
    │   └──────────────────────────────┘               │
    │                                                  │
    │   D-Cell Battery Pack                            │
    │   ┌──────────────┐                               │
    │   │ + (6V) ──→ VM│                               │
    │   │ - (GND) ─→ GND + Pi GND (common ground)     │
    │   └──────────────┘                               │
    │                                                  │
    └──────────────────────────────────────────────────┘
```

## TB6612FNG Pin-by-Pin

| TB6612FNG Pin | Connects To | Wire Gauge | Notes |
|---------------|-------------|------------|-------|
| **VM** | Battery + (6V from D cells) | 22 AWG | Motor supply voltage. Must match motor rating. |
| **VCC** | Pi 3.3V | 26 AWG | Logic supply. Determines logic HIGH level. |
| **GND** | Pi GND + Battery GND | 22 AWG | **Common ground is critical** — both power sources must share ground. |
| **STBY** | Tied to VCC (3.3V) | 26 AWG | Standby pin — tie HIGH to enable the driver. Can connect to GPIO for software sleep mode (v2.0). |
| **AIN1** | Pi GPIO 17 | 26 AWG | Motor A (left) direction input 1 |
| **AIN2** | Pi GPIO 27 | 26 AWG | Motor A (left) direction input 2 |
| **PWMA** | Pi GPIO 12 | 26 AWG | Motor A (left) speed — hardware PWM capable pin |
| **AO1** | Left motor terminal + | 22 AWG | Motor A output 1 |
| **AO2** | Left motor terminal - | 22 AWG | Motor A output 2 |
| **BIN1** | Pi GPIO 22 | 26 AWG | Motor B (right) direction input 1 |
| **BIN2** | Pi GPIO 23 | 26 AWG | Motor B (right) direction input 2 |
| **PWMB** | Pi GPIO 13 | 26 AWG | Motor B (right) speed — hardware PWM capable pin |
| **BO1** | Right motor terminal + | 22 AWG | Motor B output 1 |
| **BO2** | Right motor terminal - | 22 AWG | Motor B output 2 |

### Direction control truth table

| AIN1/BIN1 | AIN2/BIN2 | PWM | Motor action |
|-----------|-----------|-----|-------------|
| HIGH | LOW | PWM duty | Forward at PWM speed |
| LOW | HIGH | PWM duty | Backward at PWM speed |
| LOW | LOW | X | Coast (free spin) |
| HIGH | HIGH | X | Brake (short circuit) |

The software (`driver.py`) uses gpiozero's `Motor` class which handles this automatically.

## GPIO Pin Map

All pins use **BCM numbering** (not physical board pin numbers).

| BCM Pin | Physical Pin | Function | TB6612FNG Pin |
|---------|-------------|----------|---------------|
| 17 | 11 | Left motor forward | AIN1 |
| 27 | 13 | Left motor backward | AIN2 |
| 12 | 32 | Left motor PWM | PWMA |
| 22 | 15 | Right motor forward | BIN1 |
| 23 | 16 | Right motor backward | BIN2 |
| 13 | 33 | Right motor PWM | PWMB |
| 3.3V | 1 or 17 | Logic power | VCC + STBY |
| GND | 6, 9, 14, 20, 25, 30, 34, 39 | Common ground | GND |

**Note:** GPIO 12 and 13 are the Pi's hardware PWM pins (PWM0 and PWM1). This is intentional — hardware PWM gives smoother motor control than software PWM.

## Base-to-Body Connector

### What crosses the interface

10 wires across 2 connectors (2x JST-XH 5-pin), split by motor side:

**5-pin JST-XH "L" (left motor side):**

| Pin | Signal | Direction | Gauge |
|-----|--------|-----------|-------|
| 1 | AIN1 (GPIO 17) | Body → Base | 26 AWG |
| 2 | AIN2 (GPIO 27) | Body → Base | 26 AWG |
| 3 | PWMA (GPIO 12) | Body → Base | 26 AWG |
| 4 | VCC (3.3V) | Body → Base | 26 AWG |
| 5 | GND | Body → Base | 22 AWG |

**5-pin JST-XH "R" (right motor side):**

| Pin | Signal | Direction | Gauge |
|-----|--------|-----------|-------|
| 1 | BIN1 (GPIO 22) | Body → Base | 26 AWG |
| 2 | BIN2 (GPIO 23) | Body → Base | 26 AWG |
| 3 | PWMB (GPIO 13) | Body → Base | 26 AWG |
| 4 | VCC (3.3V) | Body → Base | 26 AWG |
| 5 | GND | Body → Base | 22 AWG |

**Why 2x 5-pin instead of a single large connector:**
- Each connector is self-contained per motor side — easy to debug one side at a time
- Redundant VCC/GND on both connectors for robust power delivery
- Symmetric pinout pattern (same layout, just left vs right)
- Avoids using a 6-pin JST-XH, which is already used for the head LED connector — eliminates risk of swapping connectors between head and base

**Note:** Battery GND ties to Pi GND via the GND pins on either connector. Both reach the same base breadboard GND rail, establishing the critical common ground between motor power and Pi logic.

### Physical routing

```
    Body barrel bottom (webcam box)
    ┌─────────────────────┐
    │  ·  ·  ·  ·  ·  ·  │ ← wires exit box through a hole in the bottom
    └────────┼────────────┘
             │
     ┌───────┴────────┐
     │ 2x JST-XH 5p  │  ← mating connectors at base-to-body interface
     └───────┬────────┘
             │
    Base interior
```

- Route both JST-XH harnesses through a slot in the box bottom / barrel floor
- The two 5-pin connectors disconnect cleanly to separate base from body
- Strain-relieve with a zip tie inside the base

## Assembly Sequence

### Phase 1: Motor preparation

1. **Open the base** — remove bottom access panel screws
2. **Inspect motors** — check that both spin freely, no stripped gears
3. **Test motors** — apply 3-4.5V from a bench supply or 3xAA to each motor individually; verify both spin and drive their wheels
4. **Prepare motor wires** — strip existing wire stubs or solder new 22 AWG wires (~100 mm each) to motor terminals
5. **Label motors** — mark left and right (when looking from the rear of the robot). Use tape flags or different colored heat shrink
6. **Note polarity** — for each motor, record which wire/terminal gives forward motion (away from you when robot faces forward). This maps to AO1/BO1.

### Phase 2: TB6612FNG mounting and wiring

7. **Mount TB6612FNG** — adhesive foam tape or standoff in the base interior, positioned near motors
8. **Wire motors to TB6612FNG** — connect motor L to AO1/AO2 and motor R to BO1/BO2
9. **Wire battery pack to TB6612FNG** — connect battery + to VM, battery - to GND
10. **Tie STBY to VCC** — short jumper wire on the TB6612FNG board

### Phase 3: Signal wiring to body

11. **Prepare two 5-wire harnesses** — for each JST-XH 5-pin connector, cut 3x 26 AWG signal wires + 1x 26 AWG VCC + 1x 22 AWG GND, ~250 mm (10") each
12. **Crimp JST-XH 5-pin connectors** — one "L" (AIN1, AIN2, PWMA, VCC, GND) and one "R" (BIN1, BIN2, PWMB, VCC, GND)
13. **Connect harness wires to TB6612FNG** — signal wires to control pins, VCC to logic power, GND to ground rail
14. **Route wires** — bundle neatly, strain-relieve at pass-through point
15. **Close the base** — replace access panel

### Phase 4: Body-side connections and test

16. **Connect to Pi GPIO** — wire from the body side of the connector to the Pi's GPIO header (directly or via breadboard)
17. **Connect common ground** — ensure battery GND is connected to Pi GND through the connector
18. **Test with motor_test.py:**
    ```bash
    EMIGLIO_HARDWARE_MODE=real uv run python scripts/motor_test.py
    ```
19. **Verify directions** — "Forward" should move both wheels to drive the robot forward. If a motor spins backward, swap its AO1/AO2 (or BO1/BO2) wires at the TB6612FNG.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Motors don't spin | STBY pin not tied HIGH | Connect STBY to VCC |
| Motors don't spin | No common ground | Verify battery GND and Pi GND are connected |
| One motor works, other doesn't | Loose motor wire | Check solder joints at motor terminals |
| Motor spins wrong direction | Wires swapped | Swap AO1/AO2 or BO1/BO2 at the TB6612FNG |
| Motors stutter or are weak | Low battery voltage | Replace batteries; check VM voltage with multimeter (should be ~6V) |
| Pi resets when motors start | Power draw pulling down Pi supply | Verify separate power supplies; check common ground |
| Grinding noise from gearbox | Dry gears | Apply small amount of silicone grease to gear teeth |

## Dependency on Electronics Workstream

The following details are owned by `develop-electronics` and should be finalized there:

- [ ] Confirm TB6612FNG GPIO pin assignments (currently per config.py defaults)
- [ ] Confirm motor voltage rating matches 4xAA (6V)
- [ ] Decide whether STBY pin should be GPIO-controlled (software sleep) or hard-tied HIGH
- [ ] Full circuit schematic with decoupling capacitors on motor power
- [ ] Whether to add flyback diodes on motor outputs (TB6612FNG has internal ones, but external ones add protection)
