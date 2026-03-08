# Raspberry Pi 5 GPIO Pinout — Emiglio Allocation

All pin numbers use BCM (Broadcom) numbering. The Pi 5 has the same 40-pin header as the Pi 4B.

## Allocated Pins

### Motor Control (TB6612FNG)

| Signal | BCM GPIO | Physical Pin | Direction | Wire Gauge | Notes |
|--------|----------|-------------|-----------|------------|-------|
| AIN1 (Left Forward) | 17 | 11 | Output | 26 AWG | Logic high = forward |
| AIN2 (Left Backward) | 27 | 13 | Output | 26 AWG | Logic high = backward |
| PWMA (Left Speed) | 12 | 32 | Output (PWM) | 26 AWG | Hardware PWM0 channel |
| BIN1 (Right Forward) | 22 | 15 | Output | 26 AWG | Logic high = forward |
| BIN2 (Right Backward) | 23 | 16 | Output | 26 AWG | Logic high = backward |
| PWMB (Right Speed) | 13 | 33 | Output (PWM) | 26 AWG | Hardware PWM1 channel |

### Power Pins

| Pin | Physical | Usage | Wire Gauge |
|-----|----------|-------|------------|
| 3.3V | 1 or 17 | TB6612FNG VCC + STBY | 26 AWG |
| 5V | 2 or 4 | PAM8403 VCC | 22 AWG |
| GND | 6, 9, 14, 20, 25, 30, 34, 39 | Common ground bus | 22 AWG |

### LED Eye (TBD)

| Signal | BCM GPIO | Physical Pin | Notes |
|--------|----------|-------------|-------|
| LED anode | TBD | TBD | Via 220-330 ohm resistor, 3.3V logic |

### Unallocated / Available

GPIO 4, 5, 6, 16, 19, 20, 21, 24, 25, 26 are free for future use (sensors, servos, NeoPixels, etc.)

## 40-Pin Header Visual

```
                    Pi 5 GPIO Header (top view, USB ports at bottom)
                    ┌─────────────────────────────────┐
              3.3V  │ (1)  ●  ●  (2)  │ 5V            <- Power
     [TB6612 VCC]   │      ↕     ↕     │ [PAM8403 VCC]
                    │ (3)  ○  ●  (4)  │ 5V
              SDA1  │         ↕        │
                    │ (5)  ○  ●  (6)  │ GND            <- Ground bus
              SCL1  │         ↕        │ [Common GND]
                    │ (7)  ○  ○  (8)  │ TXD
              GPIO4 │                  │ GPIO14
                    │ (9)  ●  ○  (10) │ RXD
              GND   │                  │ GPIO15
                    │ (11) ●  ○  (12) │ GPIO18
  [AIN1] GPIO17     │ ←              │
                    │ (13) ●  ●  (14) │ GND
  [AIN2] GPIO27     │ ←    ↕        │
                    │ (15) ●  ○  (16) │ GPIO23   [BIN2] →
  [BIN1] GPIO22     │ ←              │ ←
                    │ (17) ●  ○  (18) │ GPIO24
              3.3V  │                  │
                    │ (19) ○  ○  (20) │ GND
              MOSI  │         ↕        │
                    │ (21) ○  ○  (22) │ GPIO25
              MISO  │                  │
                    │ (23) ○  ○  (24) │ GPIO8
              SCLK  │                  │ CE0
                    │ (25) ●  ○  (26) │ GPIO7
              GND   │                  │ CE1
                    │ (27) ○  ○  (28) │ GPIO1
              ID_SD │                  │ ID_SC
                    │ (29) ○  ●  (30) │ GND
              GPIO5 │         ↕        │
                    │ (31) ○  ●  (32) │ GPIO12   [PWMA] →
              GPIO6 │         ↕        │ ← Hardware PWM0
                    │ (33) ●  ●  (34) │ GND
  [PWMB] GPIO13    │ ←    ↕        │
              PWM1  │                  │
                    │ (35) ○  ○  (36) │ GPIO16
                    │                  │
                    │ (37) ○  ○  (38) │ GPIO20
              GPIO26│                  │
                    │ (39) ●  ○  (40) │ GPIO21
              GND   │                  │
                    └─────────────────────────────────┘
                    ● = allocated    ○ = available
```

## Notes

- GPIOs 12 and 13 are hardware PWM pins — essential for smooth motor speed control
- STBY (standby) is tied to VCC (always enabled); could be moved to a GPIO for software sleep mode (v2.0)
- Pi 5 uses the RP1 I/O controller — gpiozero works the same as Pi 4B
- All motor GPIOs are directly routed to the base via the 9-wire body-to-base connector
