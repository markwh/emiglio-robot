# Emiglio Assembly Documentation

Physical build documentation for converting the vintage Emiglio toy robot into an AI-powered robot.

## Robot Sections

The robot splits into three main sections, assembled bottom-up:

1. **Locomotion base** — Black GP Toys platform with two DC motors (differential drive)
2. **Body barrel** — White cylindrical body housing the Pi, motor driver, amplifier, and power
3. **Head dome** — Sensors and I/O: camera, microphone, speaker, LED eyes

## Documents

### Component Mounting

- [Head Components](mounting/head-components.md) — Camera, mic, speaker, LED placement inside the head dome. Includes cable routing plan, neck connector strategy, and measurements checklist.
- [Body Barrel](mounting/body-barrel.md) — Pi 5 mounting, breadboard, PAM8403 placement, oatmeal canister sled concept, power input, and cable junction layout.
- [Base / Locomotion](mounting/base-locomotion.md) — Motor layout, TB6612FNG driver placement, battery pack mounting, and base-to-body cable interface.

### Build Guides

- [Head Wiring](build-guide/head-wiring.md) — Electrical connections between head components and the Pi/amplifier in the body. Wiring diagram, connector pinouts, and assembly sequence.
- [Body Wiring](build-guide/body-wiring.md) — Master wiring diagram, GPIO allocation, PAM8403 audio chain, power distribution, breadboard layout, and full integration assembly sequence.
- [Base Wiring](build-guide/base-wiring.md) — Motor-to-TB6612FNG wiring, GPIO pin map, base-to-body connector pinout, and step-by-step assembly with troubleshooting.
- [Pi Setup](build-guide/pi-setup.md) — First-timer walkthrough: flashing the OS, SSH, installing the emiglio stack, and testing the web UI.
- **[Base Platform Build](build-guide/base-platform-build.md)** — End-to-end guide: from opening the base to driving the robot from your laptop via the web UI joystick.

### Findings

- [Base Clutch Mechanism](findings/base-clutch-mechanism.md) — One-way clutch on drive axle prevents reverse drive. **Cross-workstream impact** — affects software locomotion assumptions.

### Reference

- [Tools & Materials](tools-materials.md) — Tools needed and consumables/parts shopping list.
- `photos/` — Build progress photos (to be added as assembly progresses).

## Current Status

- **Head:** Planning complete. Waiting on physical measurements and parts.
- **Body:** Planning complete. Central hub tying head and base together; canister sled concept documented.
- **Base:** Planning complete. Motors in place; needs measurements, wire prep, and TB6612FNG + battery mounting.
- **All sections** waiting on: Pi 5 delivery, parts purchase, and physical measurements.

## Build Order (Recommended)

1. **Bench test all electronics** outside the robot first (camera, mic, speaker, motors with Pi)
2. **Head assembly** — mount camera, mic, wire speaker, LED, install neck connector
3. **Body assembly** — mount Pi, motor driver, amplifier, power, route cables
4. **Integration** — connect head to body, body to base, full system test
5. **Close up** — secure head, tidy cables, final aesthetic touches

## Cross-References

- Circuit design and schematics → `develop-electronics` branch
- Software and configuration → `develop-software` branch
- Video context → `context/screenshots/` and `context/cleaned-transcript.md`
