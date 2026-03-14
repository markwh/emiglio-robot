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
│                            GPIO 25 (pin 22) ──→ E                   │
│                            GPIO 5  (pin 29) ──→ E                   │
│                            GPIO 6  (pin 31) ──→ E                   │
└─────────────────────────────────────────────────────────────────────┘
     │  │  │         │  │  │  │  │  │     │ │ │ │     │  │        │
     A  B  │         │  │  │  │  │  │     E E E E     F  G        H
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
                                      │  3.5mm plug      │ ◄── Neck audio connector
                                      └────┬────────┬────┘
                                           │        │
                                      ┌────┴────────┴────┐
                                      │  3.5mm jack      │ ◄── Mounted in right eye hole
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


── E: LEDs (4x 5mm red) ──────────────────────────────────────────────────────

  Pi GPIO 24 (pin 18) ──── 26 AWG ──→ 220Ω ──→ LED+ ──→ LED- ──→ GND  (Right eye)
  Pi GPIO 25 (pin 22) ──── 26 AWG ──→ 220Ω ──→ LED+ ──→ LED- ──→ GND  (Left eye)
  Pi GPIO 5  (pin 29) ──── 26 AWG ──→ 220Ω ──→ LED+ ──→ LED- ──→ GND  (Right head panel)
  Pi GPIO 6  (pin 31) ──── 26 AWG ──→ 220Ω ──→ LED+ ──→ LED- ──→ GND  (Left head panel)

  All 4 LEDs share a common GND wire.
  Routed via JST-XH 6-pin neck connector (pins 1-4: signals, pin 5: shared GND).
  220Ω resistors soldered at LED end (in head) — connector carries logic-level signals only.

  Current per LED: (3.3V - ~2.0V) / 220Ω ≈ 6 mA
  Total LED current: ~24 mA


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
| 4 | PAM8403 L-OUT+ | 3.5mm plug tip | Speaker + | 22 AWG | Red | Body → neck (3.5mm) |
| 5 | PAM8403 L-OUT- | 3.5mm plug sleeve | Speaker - | 22 AWG | Black | Body → neck (3.5mm) |
| 6 | 3.5mm jack tip | Speaker + | Speaker + | 22 AWG | Red | Neck → head |
| 7 | 3.5mm jack sleeve | Speaker - | Speaker - | 22 AWG | Black | Neck → head |
| 8 | Pi GPIO 24 (pin 18) | JST-XH pin 1 | Right eye LED | 26 AWG | White | Body → neck |
| 9 | Pi GPIO 25 (pin 22) | JST-XH pin 2 | Left eye LED | 26 AWG | Yellow | Body → neck |
| 10 | Pi GPIO 5 (pin 29) | JST-XH pin 3 | Right panel LED | 26 AWG | Blue | Body → neck |
| 11 | Pi GPIO 6 (pin 31) | JST-XH pin 4 | Left panel LED | 26 AWG | Green | Body → neck |
| 12 | Pi GND | JST-XH pin 5 | LED ground (shared) | 26 AWG | Black | Body → neck |
| 13 | Pi 3.3V (pin 1) | TB6612FNG VCC | +3.3V logic | 26 AWG | Red | Body breadboard |
| 14 | Pi 3.3V (pin 1) | TB6612FNG STBY | +3.3V enable | 26 AWG | Red | Jumper on breadboard |
| 15 | Pi GND | TB6612FNG GND | Logic ground | 22 AWG | Black | Body breadboard |
| 16 | Pi GPIO 17 (pin 11) | Screw term. #1 → AIN1 | Left fwd | 26 AWG | White | Body → base |
| 17 | Pi GPIO 27 (pin 13) | Screw term. #2 → AIN2 | Left bwd | 26 AWG | Gray | Body → base |
| 18 | Pi GPIO 12 (pin 32) | Screw term. #3 → PWMA | Left speed | 26 AWG | Yellow | Body → base |
| 19 | Pi GPIO 22 (pin 15) | Screw term. #4 → BIN1 | Right fwd | 26 AWG | Blue | Body → base |
| 20 | Pi GPIO 23 (pin 16) | Screw term. #5 → BIN2 | Right bwd | 26 AWG | Green | Body → base |
| 21 | Pi GPIO 13 (pin 33) | Screw term. #6 → PWMB | Right speed | 26 AWG | Orange | Body → base |
| 22 | Pi 3.3V | Screw term. #7 → TB6612 VCC | Logic power | 26 AWG | Red | Body → base |
| 23 | Pi GND | Screw term. #8 → TB6612 GND | Logic GND | 22 AWG | Black | Body → base |
| 24 | Battery +6V | TB6612FNG VM | Motor power | 22 AWG | Red | Base |
| 25 | Battery GND | Screw term. #9 → Pi GND | Common ground | 22 AWG | Black | Base → body |
| 26 | TB6612FNG AO1 | Left motor + | Motor drive | 22 AWG | — | Base |
| 27 | TB6612FNG AO2 | Left motor - | Motor drive | 22 AWG | — | Base |
| 28 | TB6612FNG BO1 | Right motor + | Motor drive | 22 AWG | — | Base |
| 29 | TB6612FNG BO2 | Right motor - | Motor drive | 22 AWG | — | Base |
| 30 | Pi USB-A | USB extension → Camera | USB 2.0 | — | — | Body → neck → head |
| 31 | Pi USB-A | USB extension → Microphone | USB 2.0 | — | — | Body → neck → head |

**Total: 31 connections** (25 wires + 2 USB cables + 3.5mm aux cable + 3.5mm neck audio + JST-XH 6-pin LED connector)

## Physical Layout by Zone

### Head (detachable via neck)
- USB webcam (left eye socket)
- USB microphone (dome interior)
- 4x 5mm red LEDs + 220Ω resistors (right eye, left eye, right panel, left panel)
- Speaker (dome, existing) — connected via 3.5mm jack in right eye hole
- 3.5mm female jack (mounted in back of right eye hole)

### Neck Interface (fully detachable)
- 1x 3.5mm audio: speaker (PAM8403 output)
- 1x JST-XH 6-pin: 4 LED signals + shared GND (1 spare)
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
| 24 | 18 | Right eye LED | LED |
| 25 | 22 | Left eye LED | LED |
| 5 | 29 | Right head panel LED | LED |
| 6 | 31 | Left head panel LED | LED |

6 GPIOs remain available. See [gpio-pinout.md](../wiring/gpio-pinout.md) for the full header map.

## Cross-References

- [Motor driver schematic](motor-driver.md) — TB6612FNG detail, truth table, software config
- [Audio amplifier schematic](audio-amplifier.md) — PAM8403 detail, power decision rationale
- [Power distribution](power-distribution.md) — power tree, wire gauge table
- [Power budget](../power/power-budget.md) — current measurements and battery life
- [GPIO pinout](../wiring/gpio-pinout.md) — full 40-pin header allocation map
- [Connectors](../wiring/connectors.md) — neck and base connector pinouts
- [Bench test plan](../testing/bench-test-plan.md) — verification steps for all subsystems
- [BOM](../components/bom.md) — full parts list
