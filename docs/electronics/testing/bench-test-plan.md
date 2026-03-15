# Bench Test Plan

Test all electronics on the workbench **before** installing inside the robot. This catches wiring errors, dead components, and magic smoke before anything is hard to reach.

## Prerequisites

- Raspberry Pi 5 with Raspberry Pi OS installed on microSD
- All components from BOM available
- Multimeter
- Breadboard + jumper wires

## Phase 1: Pi 5 Smoke Test ✅

**Goal**: Verify the Pi boots and can run the Emiglio software.

- [x] Flash Raspberry Pi OS to microSD (use Raspberry Pi Imager)
- [x] Configure WiFi and SSH during imaging (headless setup)
- [x] Insert microSD, connect USB-C power, verify boot (green LED activity)
- [x] SSH in: `ssh pi@<ip-address>`
- [x] Install project: `git clone`, `uv sync`
- [x] Run in mock mode: `EMIGLIO_HARDWARE_MODE=mock uv run python -m emiglio`
- [x] Verify web UI accessible at `http://<pi-ip>:8080`

## Phase 2: Camera + Microphone ✅

**Goal**: Verify USB peripherals work with the Pi.

- [x] Plug in USB camera
- [x] Check detection: `ls /dev/video*`
- [x] Test capture: `uv run python scripts/camera_test.py`
- [x] Verify MJPEG stream in web UI
- [x] Plug in USB microphone
- [x] Check detection: `arecord -l`
- [x] Test recording: `uv run python scripts/audio_test.py`

## Phase 3: Speaker + Amplifier ✅

**Goal**: Verify audio output chain.

- [x] Measure speaker impedance with multimeter (note value: **7.7 ohms** — labeled 8 ohm)
- [x] Wire PAM8403 on breadboard:
  - VCC -> Pi 5V
  - GND -> Pi GND
  - L-IN -> Pi 3.5mm (via aux cable)
  - L-OUT+ -> speaker +
  - L-OUT- -> speaker -
- [x] Play test audio: `aplay /usr/share/sounds/alsa/Front_Center.wav`
- [x] Adjust PAM8403 trim pot to comfortable volume
- [x] Test TTS output through web UI speaker button

## Phase 4: Motor Driver

**Goal**: Verify motor control with TB6612FNG.

- [x] Wire TB6612FNG on breadboard (see [motor-driver.md](../schematics/motor-driver.md)):
  - VCC -> Pi 3.3V
  - STBY -> Pi 3.3V
  - GND -> Pi GND
  - VM -> battery + (6V from 4x D-cells)
  - Battery GND -> Pi GND (common ground!)
  - AIN1/AIN2/PWMA -> GPIO 17/27/12
  - BIN1/BIN2/PWMB -> GPIO 22/23/13
  - AO1/AO2 -> left motor leads
  - BO1/BO2 -> right motor leads
- [x] Measure battery voltage with multimeter: **6.09 V** (expect ~6V)
- [x] Run motor test: `EMIGLIO_HARDWARE_MODE=real uv run python scripts/motor_test.py`
- [x] Verify: left motor forward, backward
- [x] Verify: right motor forward, backward
- [x] Verify: both motors simultaneous (forward, turn)
- [x] Check motor direction — if reversed, swap AO1/AO2 or BO1/BO2 wires
- [ ] Measure motor no-load current: _____ mA (deferred — need alligator clips, do at makerspace)
- [ ] Briefly measure stall current (< 1 sec!): _____ mA (deferred — need alligator clips, do at makerspace)

## Phase 5: LEDs (4x red) ✅

**Goal**: Verify all 4 GPIO-driven LEDs.

Each LED circuit: GPIO pin → 220Ω resistor → LED anode (+, long leg) → LED cathode (-) → GND

LED assemblies built with solder-seal connectors on 26 AWG wires (color-coded signal wires: white=R-eye, yellow=L-eye, blue=R-panel, green=L-panel, black=ground).

| LED | GPIO | Physical Pin | Location |
|-----|------|-------------|----------|
| Right eye | 24 | 18 | Right eye socket |
| Left eye | 25 | 22 | Left eye socket |
| Right panel | 5 | 29 | Right head panel (behind blue panel) |
| Left panel | 6 | 31 | Left head panel (behind red panel) |

- [x] Wire right eye LED on breadboard and test
- [x] Wire left eye LED on breadboard and test
- [x] Wire right panel LED on breadboard and test
- [x] Wire left panel LED on breadboard and test
- [x] Test all 4 individually via `gpiozero.LED` — all functional
- [x] Confirm brightness is adequate

## Phase 6: Full Integration Test

**Goal**: Everything running together, no conflicts.

- [ ] All components wired on breadboard simultaneously
- [ ] Run full Emiglio app: `EMIGLIO_HARDWARE_MODE=real uv run python -m emiglio`
- [ ] Test via web UI:
  - [ ] Camera stream visible
  - [ ] Motor controls work (forward, backward, left, right)
  - [ ] Record audio (speak into mic)
  - [ ] Play audio (TTS or test tone through speaker)
  - [ ] LED toggles (if wired into app)
- [ ] Check for interference: motor noise in audio, camera artifacts during motor use
- [ ] Measure total system power draw at Pi USB-C input: _____ mA

## Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Motors don't spin | Common ground missing | Connect battery GND to Pi GND |
| Motors spin wrong direction | AO/BO wires swapped | Swap motor + and - leads |
| Motor speed is jerky | Software PWM | Verify using GPIO 12/13 (hardware PWM) |
| No audio from speaker | PAM8403 not powered | Check 5V to VCC |
| Audio is quiet/distorted | Volume pot / impedance mismatch | Adjust trim pot, check speaker ohms |
| Camera not detected | USB power issue | Try different USB port |
| Pi won't boot | Insufficient power supply | Use official Pi 5 PSU (5V 3A+) |
