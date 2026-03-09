# Audio Amplifier Circuit — PAM8403

Amplifies the Pi's audio output to drive the existing speaker in the head dome.

## Circuit Diagram

```
    Raspberry Pi 5                    PAM8403 Board
  ┌───────────────┐              ┌──────────────────┐
  │               │              │                  │
  │  3.5mm jack ──┼── aux cable ─┼→ L-IN  (or R-IN)│
  │               │              │                  │
  │  5V (pin 2) ──┼── 22 AWG ───┼→ VCC (5V)       │
  │               │              │                  │
  │  GND (pin 6) ─┼── 22 AWG ───┼→ GND            │
  │               │              │    ┌── VOL POT   │
  └───────────────┘              │    │             │
                                 │  L-OUT+ ────────┼──→ Speaker +
                                 │  L-OUT- ────────┼──→ Speaker -
                                 │                  │
                                 └──────────────────┘
                                         │
                                    (via JST-XH 4-pin
                                     neck connector
                                     to head speaker)
```

## Signal Chain

```
Pi 3.5mm audio out
    │
    ▼
Short 3.5mm aux cable (~150mm)
    │
    ▼
PAM8403 line input (L channel)
    │
    ▼ (amplified, up to 3W)
    │
JST-XH 4-pin neck connector (pins 1-2)
    │
    ▼
Speaker in head dome
```

## PAM8403 Specs

| Parameter | Value |
|-----------|-------|
| Supply voltage | 2.5-5.5V |
| Output power | 3W per channel @ 4 ohm, 5V |
| Quiescent current | ~5 mA |
| THD+N | 0.1% typical |
| Channels | 2 (using 1 for mono speaker) |
| Efficiency | ~90% (Class D) |

## Connections

| PAM8403 Pin | Connection | Notes |
|-------------|-----------|-------|
| VCC | Pi 5V (pin 2 or 4) | Via 22 AWG red wire |
| GND | Pi GND rail | Via 22 AWG black wire |
| L-IN / R-IN | Pi 3.5mm jack | Via short aux cable |
| L-OUT+ | Speaker + | Through neck JST connector |
| L-OUT- | Speaker - | Through neck JST connector |

## Power Source Decision

**Pi 5V rail confirmed** as power source for the PAM8403 (EL-02 resolved).

- Worst-case total USB-C draw (all peripherals + loud audio) is ~2.4A, well within the 3A PSU budget
- PAM8403 Class D efficiency (~90%) means minimal waste heat
- Speech/TTS through a small speaker draws ~200-300mA typical, far below the 600mA peak spec
- Motors run on separate battery domain, so motor activity doesn't affect 5V rail headroom
- A separate power supply would add wiring complexity with no benefit at these current levels

## Notes

- The PAM8403 board includes a small trim potentiometer for volume adjustment
- Speaker impedance should be measured with multimeter before first power-on (expect 4-8 ohm)
- Pi 5 3.5mm output is PWM-based — adequate for speech/TTS, not audiophile quality
- For v2.0, consider I2S DAC for digital audio path (better quality, fewer artifacts)
- Mount the PAM8403 on the breadboard inside the body barrel
- Keep the aux cable short to minimize noise pickup from motor PWM signals
