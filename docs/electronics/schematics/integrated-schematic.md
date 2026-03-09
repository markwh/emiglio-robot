# Integrated Circuit Schematic — Emiglio v1.0

Complete wiring reference for all electrical subsystems. This is the master document (EL-04) — individual subsystem schematics remain as detailed references.

## Full System Diagram

```
═══════════════════════════════════════════════════════════════════════════════
                              POWER SOURCES
═══════════════════════════════════════════════════════════════════════════════

  USB-C PSU (5V 3A+)                        4x D-Cell Batteries (6V)
  ┌─────────────┐                           ┌─────────────────┐
  │  5V   GND   │                           │  +6V     GND    │
  └──┬─────┬────┘                           └──┬────────┬─────┘
     │     │                                   │        │
     │     │    ┌──────────────────────────────┼────────┤
     │     │    │       COMMON GROUND BUS      │        │
     │     │    │  ┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄┄  │        │
     │     └────┼──── GND (22 AWG) ◄───────────┼────────┘
     │          │                              │
     ▼          ▼                              ▼
═══════════════════════════════════════════════════════════════════════════════
                           RASPBERRY PI 5
═══════════════════════════════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────────────────┐
│                         RASPBERRY PI 5                              │
│                                                                     │
│  POWER OUT                 GPIO OUT                   PERIPHERALS   │
│  ─────────                 ────────                   ───────────   │
│  5V  (pin 2) ──→ A        GPIO 17 (pin 11) ──→ D     USB ──→ F    │
│  3.3V (pin 1) ──→ B       GPIO 27 (pin 13) ──→ D     USB ──→ G    │
│  GND (pin 6+) ──→ bus     GPIO 12 (pin 32) ──→ D     3.5mm ──→ H  │
│                            GPIO 22 (pin 15) ──→ D                   │
│  USB-C ◄── 5V 3A PSU      GPIO 23 (pin 16) ──→ D                   │
│                            GPIO 13 (pin 33) ──→ D                   │
│                            GPIO 24 (pin 18) ──→ E                   │
└─────────────────────────────────────────────────────────────────────┘
     │  │  │         │  │  │  │  │  │         │     │  │        │
     A  B  │         │  │  │  │  │  │         E     F  G        H
     │  │  │         │  │  │  │  │  │         │     │  │        │
     ▼  ▼  ▼         ▼  ▼  ▼  ▼  ▼  ▼         ▼     ▼  ▼        ▼

═══════════════════════════════════════════════════════════════════════════════
  A: AUDIO AMP        B: MOTOR DRIVER          E: LED       F/G: USB    H: AUX
═══════════════════════════════════════════════════════════════════════════════


── A: PAM8403 Audio Amplifier ─────────────────────────────────────────────────

  Pi 5V (pin 2) ────── 22 AWG red ────────→ PAM8403 VCC
  Pi GND ───────────── 22 AWG black ──────→ PAM8403 GND
  Pi 3.5mm jack ────── aux cable (150mm) ─→ PAM8403 L-IN
                                              │
                                         ┌────┴────┐
                                         │ PAM8403 │
                                         │ Class D │
                                         │  amp    │
                                         └────┬────┘
                                              │
                                         L-OUT+  L-OUT-
                                           │        │
                                      ┌────┴────────┴────┐
                                      │  JST-XH 4-pin    │
                                      │  pins 1-2        │ ◄── Neck connector
                                      └────┬────────┬────┘
                                           │        │
                                       Speaker+  Speaker-
                                      ┌────┴────────┴────┐
                                      │   Head Speaker   │
                                      │   (4-8 ohm)      │
                                      └──────────────────┘


── B: TB6612FNG Motor Driver ──────────────────────────────────────────────────

  Pi 3.3V (pin 1) ──── 26 AWG red ──→ TB6612FNG VCC ─┬─→ STBY (tied high)
  Pi GND ────────────── 22 AWG black ──→ TB6612FNG GND│
  Battery +6V ─────── 22 AWG red ──→ TB6612FNG VM    │
  Battery GND ─────── 22 AWG black ──→ Pi GND bus    │  ◄── CRITICAL common ground
                                                      │
                                    ┌─────────────────┴──────────────────┐
                                    │            TB6612FNG                │
                                    │                                    │
                                    │  Left Motor (A)   Right Motor (B)  │
                                    │  AIN1 ◄── GPIO 17  BIN1 ◄── GPIO 22│
                                    │  AIN2 ◄── GPIO 27  BIN2 ◄── GPIO 23│
                                    │  PWMA ◄── GPIO 12  PWMB ◄── GPIO 13│
                                    │   │                 │              │
                                    │  AO1/AO2           BO1/BO2        │
                                    └───┬──┬──────────────┬──┬──────────┘
                                        │  │              │  │
                          ┌─────────── via 9-wire base connector ──────────┐
                          │  (screw terminal block)                        │
                          │                                                │
                     ┌────┴────┐                                    ┌─────┴───┐
                     │  Left   │                                    │  Right  │
                     │  Motor  │                                    │  Motor  │
                     │  + ← AO1│                                    │  + ← BO1│
                     │  - ← AO2│                                    │  - ← BO2│
                     └─────────┘                                    └─────────┘


── E: LED Eye ─────────────────────────────────────────────────────────────────

  Pi GPIO 24 (pin 18) ──── 26 AWG ──→ 220 ohm resistor ──→ LED anode (+)
  Pi GND ─────────────────────────────────────────────────→ LED cathode (-)
      │                                                        │
      └─── via JST-XH 4-pin neck connector (pins 3-4) ────────┘

  Current: (3.3V - ~2.0V LED drop) / 220 ohm ≈ 6 mA (safe, visible)


── F/G: USB Peripherals ───────────────────────────────────────────────────────

  Pi USB-A port 1 ──→ USB extension ──→ [neck] ──→ USB Webcam (left eye)
  Pi USB-A port 2 ──→ USB extension ──→ [neck] ──→ USB Microphone (head dome)

  Both pass through neck as detachable USB-A male/female pairs.
```

## Connection Summary Table

Every wire in the system:

| # | From | To | Signal | Gauge | Color | Route |
|---|------|----|--------|-------|-------|-------|
| 1 | Pi 5V (pin 2) | PAM8403 VCC | +5V power | 22 AWG | Red | Body breadboard |
| 2 | Pi GND (pin 6) | PAM8403 GND | Ground | 22 AWG | Black | Body breadboard |
| 3 | Pi 3.5mm jack | PAM8403 L-IN | Audio signal | — | — | Aux cable (150mm) |
| 4 | PAM8403 L-OUT+ | JST-XH pin 1 | Speaker + | 22 AWG | Red | Body → neck |
| 5 | PAM8403 L-OUT- | JST-XH pin 2 | Speaker - | 22 AWG | Black | Body → neck |
| 6 | JST-XH pin 1 | Speaker + | Speaker + | 22 AWG | Red | Neck → head |
| 7 | JST-XH pin 2 | Speaker - | Speaker - | 22 AWG | Black | Neck → head |
| 8 | Pi GPIO 24 (pin 18) | JST-XH pin 3 | LED signal | 26 AWG | White | Body → neck |
| 9 | Pi GND | JST-XH pin 4 | LED ground | 26 AWG | Green | Body → neck |
| 10 | JST-XH pin 3 | 220 ohm resistor → LED+ | LED signal | 26 AWG | White | Neck → head |
| 11 | JST-XH pin 4 | LED cathode (-) | LED ground | 26 AWG | Green | Neck → head |
| 12 | Pi 3.3V (pin 1) | TB6612FNG VCC | +3.3V logic | 26 AWG | Red | Body breadboard |
| 13 | Pi 3.3V (pin 1) | TB6612FNG STBY | +3.3V enable | 26 AWG | Red | Jumper on breadboard |
| 14 | Pi GND | TB6612FNG GND | Logic ground | 22 AWG | Black | Body breadboard |
| 15 | Pi GPIO 17 (pin 11) | Screw term. #1 → AIN1 | Left fwd | 26 AWG | White | Body → base |
| 16 | Pi GPIO 27 (pin 13) | Screw term. #2 → AIN2 | Left bwd | 26 AWG | Gray | Body → base |
| 17 | Pi GPIO 12 (pin 32) | Screw term. #3 → PWMA | Left speed | 26 AWG | Yellow | Body → base |
| 18 | Pi GPIO 22 (pin 15) | Screw term. #4 → BIN1 | Right fwd | 26 AWG | Blue | Body → base |
| 19 | Pi GPIO 23 (pin 16) | Screw term. #5 → BIN2 | Right bwd | 26 AWG | Green | Body → base |
| 20 | Pi GPIO 13 (pin 33) | Screw term. #6 → PWMB | Right speed | 26 AWG | Orange | Body → base |
| 21 | Pi 3.3V | Screw term. #7 → TB6612 VCC | Logic power | 26 AWG | Red | Body → base |
| 22 | Pi GND | Screw term. #8 → TB6612 GND | Logic GND | 22 AWG | Black | Body → base |
| 23 | Battery +6V | TB6612FNG VM | Motor power | 22 AWG | Red | Base |
| 24 | Battery GND | Screw term. #9 → Pi GND | Common ground | 22 AWG | Black | Base → body |
| 25 | TB6612FNG AO1 | Left motor + | Motor drive | 22 AWG | — | Base |
| 26 | TB6612FNG AO2 | Left motor - | Motor drive | 22 AWG | — | Base |
| 27 | TB6612FNG BO1 | Right motor + | Motor drive | 22 AWG | — | Base |
| 28 | TB6612FNG BO2 | Right motor - | Motor drive | 22 AWG | — | Base |
| 29 | Pi USB-A | USB extension → Camera | USB 2.0 | — | — | Body → neck → head |
| 30 | Pi USB-A | USB extension → Microphone | USB 2.0 | — | — | Body → neck → head |

**Total: 30 connections** (24 wires + 2 USB cables + 3.5mm aux cable + JST-XH connector with 4 signals)

## Physical Layout by Zone

### Head (detachable via neck)
- USB webcam (left eye socket)
- USB microphone (dome interior)
- 5mm red LED + 220 ohm resistor (right eye socket)
- Speaker (dome, existing)

### Neck Interface (fully detachable)
- 1x JST-XH 4-pin: speaker (2 pins) + LED (2 pins)
- 2x USB-A extension: camera + microphone

### Body Barrel (main electronics)
- Raspberry Pi 5 (mounted on standoffs)
- Half-size breadboard (foam-taped to barrel wall)
  - PAM8403 amplifier board
  - TB6612FNG logic connections (VCC, STBY, GND, signal breakout)
- USB-C PSU cable entry (rear grommet)
- 10-pos screw terminal block (body-to-base interface)

### Base Platform
- TB6612FNG motor driver board (on small breadboard or direct-wired)
- 4x D-cell battery holder (6V)
- Left + right DC motors (existing)
- 10-pos screw terminal block (base side of body-to-base interface)

## Power Budget Summary

| Domain | Source | Typical | Peak | Headroom |
|--------|--------|---------|------|----------|
| USB-C (5V) | 5V 3A PSU | ~1.6A | ~2.4A | 0.6A at peak |
| Battery (6V) | 4x D-cell | ~600mA | ~2.4A | D-cells handle this easily |

See [power-distribution.md](power-distribution.md) and [power-budget](../power/power-budget.md) for full details.

## GPIO Allocation Summary

| BCM GPIO | Pin | Function | Subsystem |
|----------|-----|----------|-----------|
| 17 | 11 | AIN1 (left fwd) | Motor driver |
| 27 | 13 | AIN2 (left bwd) | Motor driver |
| 12 | 32 | PWMA (left speed) | Motor driver |
| 22 | 15 | BIN1 (right fwd) | Motor driver |
| 23 | 16 | BIN2 (right bwd) | Motor driver |
| 13 | 33 | PWMB (right speed) | Motor driver |
| 24 | 18 | LED eye | LED |

9 GPIOs remain available. See [gpio-pinout.md](../wiring/gpio-pinout.md) for the full header map.

## Cross-References

- [Motor driver schematic](motor-driver.md) — TB6612FNG detail, truth table, software config
- [Audio amplifier schematic](audio-amplifier.md) — PAM8403 detail, power decision rationale
- [Power distribution](power-distribution.md) — power tree, wire gauge table
- [Power budget](../power/power-budget.md) — current measurements and battery life
- [GPIO pinout](../wiring/gpio-pinout.md) — full 40-pin header allocation map
- [Connectors](../wiring/connectors.md) — neck and base connector pinouts
- [Bench test plan](../testing/bench-test-plan.md) — verification steps for all subsystems
- [BOM](../components/bom.md) — full parts list
