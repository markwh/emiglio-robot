# Power Distribution

Complete power routing for all Emiglio electrical systems.

## Power Sources

| Source | Voltage | Location | Supplies |
|--------|---------|----------|----------|
| USB-C PSU | 5V 3A+ | Body (rear entry) | Pi 5, PAM8403, USB peripherals |
| 4x D-cell batteries | 6V | Base | DC motors via TB6612FNG |

## Power Tree

```
USB-C (5V 3A+) ──→ Pi 5 USB-C port
                      │
                      ├── 5V rail (pin 2/4) ──→ PAM8403 VCC
                      │
                      ├── 3.3V rail (pin 1/17) ──→ TB6612FNG VCC
                      │                            TB6612FNG STBY
                      │
                      ├── USB ports ──→ Camera (USB)
                      │                 Microphone (USB)
                      │
                      └── GND rail ──→ PAM8403 GND
                                       TB6612FNG GND (logic)
                                       Battery GND (common ground)

4x D-cells (6V) ──→ TB6612FNG VM
                      │
                      ├── AO1/AO2 ──→ Left motor
                      ├── BO1/BO2 ──→ Right motor
                      │
                      └── Battery GND ──→ Pi GND (common ground wire)
```

## Current Budget

| Consumer | Voltage | Max Current | Typical Current | Source |
|----------|---------|-------------|-----------------|--------|
| Pi 5 (no load) | 5V | - | ~600 mA | USB-C |
| Pi 5 (with peripherals) | 5V | - | ~1.0 A | USB-C |
| USB camera | 5V | 500 mA | ~200 mA | Pi USB |
| USB microphone | 5V | 100 mA | ~50 mA | Pi USB |
| PAM8403 (idle) | 5V | - | ~5 mA | Pi 5V pin |
| PAM8403 (playing audio) | 5V | 600 mA | ~300 mA | Pi 5V pin |
| LED eye | 3.3V | 20 mA | ~15 mA | Pi GPIO |
| **Total from USB-C** | **5V** | - | **~1.6 A typ** | |
| Left motor | 6V | 1.2 A (driver limit) | ~300 mA | Battery |
| Right motor | 6V | 1.2 A (driver limit) | ~300 mA | Battery |
| **Total from batteries** | **6V** | **2.4 A peak** | **~600 mA typ** | |

## Battery Life Estimate

- D-cell capacity: ~12,000 mAh
- Typical motor draw: ~600 mA combined (mixed driving)
- Estimated runtime: ~20 hours of active motor use
- Standby (motors off): essentially zero battery drain (TB6612FNG STBY tied high but no current flows with PWM=0)

## Safety Considerations

- **No reverse polarity protection** on battery input — D-cells are physically keyed in their cases
- **TB6612FNG thermal shutdown** protects against sustained overcurrent
- **Pi 5 has its own power management** — will throttle or shut down if USB-C is underpowered
- **Common ground is critical** — without it, GPIO logic levels are unreliable and damage is possible
- Consider adding a fuse (2A fast-blow) in series with battery positive for motor short protection (v2.0)

## Wire Gauge Summary

| Run | Gauge | Reason |
|-----|-------|--------|
| Battery to TB6612FNG VM | 22 AWG | Up to 2.4A peak |
| Battery GND to Pi GND | 22 AWG | Common ground, moderate current |
| Pi 5V to PAM8403 | 22 AWG | Up to 600 mA |
| Pi 3.3V to TB6612FNG VCC | 26 AWG | Logic power, <50 mA |
| GPIO signal wires | 26 AWG | Logic level, negligible current |
| Speaker wires | 22 AWG | Up to 600 mA from amplifier |
