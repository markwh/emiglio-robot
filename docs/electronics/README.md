# Emiglio Electronics Documentation

Circuit design, wiring, components, and electrical systems for the Emiglio robot.

## System Overview

The Emiglio robot has three electrical zones connected by multi-wire interfaces:

```
┌─────────────────────┐
│       HEAD           │
│  Camera (USB)        │
│  Microphone (USB)    │
│  Speaker (2-wire)    │
│  LED eye (2-wire)    │
└────────┬────────────┘
     JST 4-pin + 2x USB
┌────────┴────────────┐
│       BODY           │
│  Raspberry Pi 5      │
│  PAM8403 amplifier   │
│  Breadboard hub      │
│  USB-C power entry   │
└────────┬────────────┘
     9-wire connector
┌────────┴────────────┐
│       BASE           │
│  TB6612FNG driver    │
│  2x DC motors        │
│  4x D-cell batteries │
└─────────────────────┘
```

## Documents

| Document | Description |
|----------|-------------|
| [schematics/motor-driver.md](schematics/motor-driver.md) | TB6612FNG circuit with Pi 5 GPIO |
| [schematics/audio-amplifier.md](schematics/audio-amplifier.md) | PAM8403 speaker amplifier circuit |
| [schematics/power-distribution.md](schematics/power-distribution.md) | Full power routing diagram |
| [components/bom.md](components/bom.md) | Bill of materials with costs and status |
| [wiring/gpio-pinout.md](wiring/gpio-pinout.md) | Complete Pi 5 GPIO allocation map |
| [wiring/connectors.md](wiring/connectors.md) | Inter-zone connector specs |
| [power/power-budget.md](power/power-budget.md) | Voltage/current calculations |
| [testing/bench-test-plan.md](testing/bench-test-plan.md) | Pre-assembly validation checklist |

## Quick Reference: GPIO Allocation

| GPIO (BCM) | Physical | Function | Zone |
|------------|----------|----------|------|
| 12 | 32 | Motor Left PWM (PWMA) | Base |
| 13 | 33 | Motor Right PWM (PWMB) | Base |
| 17 | 11 | Motor Left Forward (AIN1) | Base |
| 22 | 15 | Motor Right Forward (BIN1) | Base |
| 23 | 16 | Motor Right Backward (BIN2) | Base |
| 27 | 13 | Motor Left Backward (AIN2) | Base |
| TBD | TBD | LED eye | Head |

## Status

- [x] GPIO pin assignments defined in software
- [x] Component list drafted (see assembly docs)
- [ ] Formal schematics
- [ ] Power budget calculations
- [ ] Bench test procedures
- [ ] Connector interface specs finalized
