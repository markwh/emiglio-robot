# Power Budget

Detailed current and voltage calculations for Emiglio's two power domains.

## Domain 1: USB-C (5V)

Powers the Pi and all logic/peripheral systems.

| Consumer | Voltage | Typical (mA) | Peak (mA) | Notes |
|----------|---------|-------------|-----------|-------|
| Pi 5 core | 5V | 600 | 1200 | CPU-dependent |
| USB camera | 5V | 200 | 500 | USB 2.0 max |
| USB microphone | 5V | 50 | 100 | Small dongle |
| PAM8403 idle | 5V | 5 | 5 | Class D, very low quiescent |
| PAM8403 playing | 5V | 300 | 600 | Depends on volume + speaker impedance |
| LEDs (4x red) | 3.3V* | 24 | 24 | 4x ~6 mA each, via GPIO + 220Ω resistor |
| TB6612FNG logic | 3.3V* | 5 | 10 | VCC + STBY |
| **Total** | | **~1184** | **~2439** | |

*3.3V is derived from the Pi's onboard regulator, powered from USB-C 5V.

**Recommendation**: Use a 5V 3A USB-C supply (the official Pi 5 PSU). Provides comfortable headroom above the ~2.4A peak.

## Domain 2: Battery (6V)

Powers only the DC motors through the TB6612FNG.

| Consumer | Voltage | Typical (mA) | Peak (mA) | Notes |
|----------|---------|-------------|-----------|-------|
| Left motor | 6V | 300 | 1200 | TB6612FNG per-channel limit |
| Right motor | 6V | 300 | 1200 | TB6612FNG per-channel limit |
| **Total** | | **~600** | **~2400** | |

**Battery life at typical draw**:
- D-cell capacity: ~12,000 mAh
- 12,000 / 600 = **~20 hours** of continuous mixed driving
- Standby: effectively zero drain

## Worst-Case Scenario

Both motors stalled simultaneously:
- Stall current TBD (measure during bench test)
- TB6612FNG limits to 1.2A continuous per channel = 2.4A total
- D-cells can supply this without issue
- TB6612FNG thermal shutdown will trigger if sustained

## Measurements to Take During Bench Test

1. **Motor no-load current** — run each motor with no mechanical load, measure with multimeter in series
2. **Motor typical load current** — robot driving on flat surface
3. **Motor stall current** — hold wheel, measure briefly (< 1 second!)
4. **Speaker impedance** — multimeter across speaker terminals (expect 4-8 ohm)
5. **Total Pi system draw** — measure USB-C input current with all peripherals connected
