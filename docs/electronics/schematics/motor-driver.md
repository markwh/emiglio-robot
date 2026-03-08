# Motor Driver Circuit — TB6612FNG

Dual H-bridge motor driver connecting the Raspberry Pi 5 to two DC motors in the base.

## Circuit Diagram

```
                         Raspberry Pi 5
                    ┌──────────────────────┐
                    │                      │
                    │  GPIO 17 (pin 11) ───┼──── AIN1
                    │  GPIO 27 (pin 13) ───┼──── AIN2
                    │  GPIO 12 (pin 32) ───┼──── PWMA   (hardware PWM0)
                    │                      │
                    │  GPIO 22 (pin 15) ───┼──── BIN1
                    │  GPIO 23 (pin 16) ───┼──── BIN2
                    │  GPIO 13 (pin 33) ───┼──── PWMB   (hardware PWM1)
                    │                      │
                    │  3.3V (pin 1/17) ────┼──── VCC ─┬─ STBY
                    │                      │          │
                    │  GND (pin 6/etc) ────┼──── GND  │
                    └──────────────────────┘          │
                                                      │
                    ┌─────── TB6612FNG ───────────────┘
                    │
                    │  VCC ──── 3.3V (logic supply)
                    │  STBY ─── 3.3V (always enabled)
                    │  VM ───── +6V (battery)
                    │  GND ──── common ground
                    │
                    │  AIN1, AIN2, PWMA ──→ Motor A (left)
                    │  AO1 ───────────────→ Left motor +
                    │  AO2 ───────────────→ Left motor -
                    │
                    │  BIN1, BIN2, PWMB ──→ Motor B (right)
                    │  BO1 ───────────────→ Right motor +
                    │  BO2 ───────────────→ Right motor -
                    │
                    │  VM ◄──── 4x D-cell (6V)
                    │  GND ◄─── Battery GND ──→ Pi GND (common ground!)
                    └─────────────────────────────────

        ┌──────────┐                    ┌──────────┐
        │ Left     │                    │ Right    │
        │ Motor    │                    │ Motor    │
        │  + ← AO1 │                    │  + ← BO1 │
        │  - ← AO2 │                    │  - ← BO2 │
        └──────────┘                    └──────────┘
```

## TB6612FNG Pin Reference

| Pin | Connection | Notes |
|-----|-----------|-------|
| VCC | Pi 3.3V | Logic power (2.7-5.5V) |
| VM | Battery +6V | Motor power (4.5-13.5V) |
| GND | Common ground | Must tie Pi GND and battery GND together |
| STBY | Pi 3.3V | Tied high = enabled. Could go to GPIO for sleep mode. |
| AIN1 | GPIO 17 | Motor A direction bit 1 |
| AIN2 | GPIO 27 | Motor A direction bit 2 |
| PWMA | GPIO 12 | Motor A speed (PWM duty cycle) |
| BIN1 | GPIO 22 | Motor B direction bit 1 |
| BIN2 | GPIO 23 | Motor B direction bit 2 |
| PWMB | GPIO 13 | Motor B speed (PWM duty cycle) |
| AO1 | Left motor + | Motor A output 1 |
| AO2 | Left motor - | Motor A output 2 |
| BO1 | Right motor + | Motor B output 1 |
| BO2 | Right motor - | Motor B output 2 |

## Motor Direction Truth Table

| xIN1 | xIN2 | PWM | Result |
|------|------|-----|--------|
| HIGH | LOW | duty% | Forward at duty% speed |
| LOW | HIGH | duty% | Backward at duty% speed |
| LOW | LOW | X | Coast (free spin) |
| HIGH | HIGH | X | Brake (short motor leads) |

The software uses gpiozero's `Motor` class which handles the direction logic. Speed is controlled via PWM duty cycle (0.0-1.0).

## Electrical Specs

- **Motor supply**: 6V from 4x D-cells in series
- **Max continuous current**: 1.2A per channel (TB6612FNG limit)
- **Max peak current**: 3.2A per channel (short bursts)
- **Motor stall current**: TBD — measure during bench test (if >1.2A, limit PWM duty cycle in software)
- **Thermal protection**: Built-in on TB6612FNG

## Critical: Common Ground

The Pi GND and battery GND **must** be connected. Without a common ground reference, the TB6612FNG cannot read the Pi's GPIO logic levels. Route a 22 AWG wire from battery negative to Pi GND rail.

## Software Config

These pins are configured in `src/emiglio/config.py` as env vars:

```bash
EMIGLIO_MOTOR_LEFT_FORWARD=17
EMIGLIO_MOTOR_LEFT_BACKWARD=27
EMIGLIO_MOTOR_LEFT_ENABLE=12
EMIGLIO_MOTOR_RIGHT_FORWARD=22
EMIGLIO_MOTOR_RIGHT_BACKWARD=23
EMIGLIO_MOTOR_RIGHT_ENABLE=13
```
