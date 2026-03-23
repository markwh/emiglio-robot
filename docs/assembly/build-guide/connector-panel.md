# Connector Panel Build Guide

## Overview

The electronics enclosure (webcam box) uses a perfboard-backed connector panel to provide clean plug-in interfaces. All harnesses from the robot's head and base plug directly into the box, making it a self-contained, removable electronics module.

## Box Orientation

The box is approximately 4"L x 3.5"W x 2.5"H. The Pi 5 is mounted vertically against the left wall. The breadboard lays flat on the bottom.

```
        TOP VIEW (looking down into box, lid removed)

                  3.5" W
        ┌───────────────────┐
        │                   │
        │  Pi 5    bread-   │
        │  (vert.  board    │  4" L
        │  against (flat on │
        │  this    bottom)  │
        │  wall)            │
        │                   │
        │                   │
        └───────────────────┘
```

### Face A — Input Face (3.5"W x 2.5"H)

The face where the Pi's ports are visible on the left edge. The audio input jack is also on this face.

```
        FACE A (3.5"W x 2.5"H) — INPUT FACE
        ┌───────────────────┐
        │ ┌───┐             │
        │ │USB│             │
        │ │USB│       ◎ IN  │  2.5" H
        │ │ETH│             │
        │ │PWR│             │
        └───────────────────┘
```

| Connection | Type | Purpose |
|------------|------|---------|
| USB ports | Pi 5 built-in (4x) | USB audio adapter, camera, mic |
| Ethernet | Pi 5 built-in | Network (optional) |
| USB-C PWR | Pi 5 built-in | 5V 3A+ power input |
| ◎ IN | 3.5mm female jack | Audio from USB adapter back into box → PAM8403 input |

The USB-to-3.5mm audio adapter plugs into a Pi USB port, hangs outside the box, and its 3.5mm output connects via a short aux cable back into the audio IN jack on the same face.

### Face B — Output Face (4"L x 2.5"H)

The wall opposite the Pi. All outbound connections live here. Audio OUT is on the left, close to the shared corner with Face A's audio IN for short internal PAM8403 wiring. LEDs are above motors since LED wires route up to the head and motor wires route down to the base.

```
        FACE B (4"L x 2.5"H) — OUTPUT FACE
        (wall opposite the Pi)
        ┌──────────────────────────┐
        │                          │
        │ ◎ OUT  [LED 6p]          │  2.5" H
        │        [L 5p] [R 5p]    │
        │                          │
        └──────────────────────────┘
```

| Connection | Type | Direction | Purpose |
|------------|------|-----------|---------|
| ◎ OUT | 3.5mm female jack | Box → Head | Amplified audio from PAM8403 → head speaker |
| LED 6p | JST-XH 6-pin male | Box → Head | 4 LED signals + shared GND + spare |
| L 5p | JST-XH 5-pin male | Box → Base | Left motor control (AIN1, AIN2, PWMA, VCC, GND) |
| R 5p | JST-XH 5-pin male | Box → Base | Right motor control (BIN1, BIN2, PWMB, VCC, GND) |

## Materials

- Small piece of perfboard (~30x60mm — enough for 3 JST-XH headers in a row)
- 2x JST-XH 5-pin male through-hole headers
- 1x JST-XH 6-pin male through-hole header
- 2x 3.5mm panel-mount female jacks (TRS or TS)
- 26 AWG hookup wire (signal runs to breadboard)
- 22 AWG hookup wire (GND pins)
- Soldering iron + solder
- 5-minute epoxy
- Hot glue gun (gap-filling and strain relief only)
- Coarse sandpaper (for scuffing perfboard before epoxy)
- Box cutter / hobby knife
- Binder clips or small clamps (for clamping during epoxy cure)
- Marker
- Wire strippers

## Build Steps

### Part 1: Perfboard connector panel (Face B)

1. **Lay out the headers** on the perfboard — place all 3 JST-XH male headers with pins down, socket openings facing the same direction. Arrange them:
   - Top row: JST-XH 6-pin (LEDs)
   - Bottom row: JST-XH 5-pin (L), JST-XH 5-pin (R)
   - Leave ~3mm between headers

2. **Mark and cut the perfboard** — trace the outline with ~3mm margin on all sides. Score with a box cutter and snap, or use a saw.

3. **Solder the headers** — insert pins through the perfboard from the top (socket openings face up). Solder all pins on the back side.

4. **Bridge the GND pins** — on the back of the perfboard, connect the GND pins from all 3 headers with a solder trace or short wire jumper. This creates a single ground bus. Run one 22 AWG lead from this bus to the breadboard GND rail.

5. **Solder signal wires** — run ~100-150mm 26 AWG leads from each signal pin on the back of the perfboard. Use the color scheme:

   **LED 6-pin:**
   | Pin | Signal | Color |
   |-----|--------|-------|
   | 1 | Right eye LED (GPIO 24) | White |
   | 2 | Left eye LED (GPIO 25) | Yellow |
   | 3 | Right panel LED (GPIO 5) | Blue |
   | 4 | Left panel LED (GPIO 6) | Green |
   | 5 | LED GND (bridged) | Black |
   | 6 | Spare | — |

   **Left motor 5-pin:**
   | Pin | Signal | Color |
   |-----|--------|-------|
   | 1 | AIN1 (GPIO 17) | White |
   | 2 | AIN2 (GPIO 27) | Gray |
   | 3 | PWMA (GPIO 12) | Yellow |
   | 4 | VCC (3.3V) | Red |
   | 5 | GND (bridged) | Black |

   **Right motor 5-pin:**
   | Pin | Signal | Color |
   |-----|--------|-------|
   | 1 | BIN1 (GPIO 22) | White |
   | 2 | BIN2 (GPIO 23) | Gray |
   | 3 | PWMB (GPIO 13) | Yellow |
   | 4 | VCC (3.3V) | Red |
   | 5 | GND (bridged) | Black |

6. **Cut the window in Face B** — hold the perfboard against the outside of the box wall, trace around just the header faces (the rectangles where the plugs insert). Cut out that rectangle with a box cutter. The perfboard should be larger than the window on all sides.

7. **Test fit** — push the headers through the window from inside the box. The socket openings should sit flush with or slightly proud of the box exterior. The perfboard rests flat against the inside wall.

8. **Scuff the perfboard margin** — use coarse sandpaper on the back of the perfboard border (the area that will contact cardboard, around the headers). This gives the epoxy something to grip on the smooth FR4 surface.

9. **Epoxy the panel in place** — mix 5-minute epoxy thoroughly and apply to the perfboard margin (keep it away from header pins and sockets). Press the perfboard firmly against the inside of the box wall with headers through the window. Clamp with binder clips and let cure fully. The cardboard never takes plug/unplug force — the rigid epoxy bond and perfboard do.

10. **Hot glue for gap-filling** (optional) — after epoxy has cured, run a bead of hot glue around the edges for strain relief on the signal wires where they exit the solder joints.

### Part 2: Audio OUT jack (Face B)

11. **Mount the 3.5mm OUT jack** — cut a round hole on the left side of Face B (see diagram above). If using a panel-mount jack with a threaded barrel and nut, push the barrel through the hole and tighten the nut from inside — this is mechanically solid on its own. If the jack has no threaded mount, scuff the jack body with sandpaper and epoxy it into the hole.

12. **Wire the OUT jack inside the box:**
    - Tip → PAM8403 L-OUT+ (via breadboard)
    - Sleeve → PAM8403 L-OUT- (via breadboard)

### Part 3: Audio IN jack (Face A)

13. **Mount the 3.5mm IN jack** — cut a round hole on Face A (the input face), positioned away from the Pi ports (right side of face). Same mounting approach as the OUT jack: threaded nut if available, otherwise scuff and epoxy.

14. **Wire the IN jack inside the box:**
    - Tip → PAM8403 L-IN (via breadboard)
    - Sleeve → PAM8403 GND (via breadboard)

### Part 4: Route and dress

15. **Route all wires to the breadboard** — dress leads along the box interior walls. Keep signal wires away from the audio input wires to minimize noise pickup.

16. **Connect to breadboard:**
    - Motor and LED signal wires → jumper to corresponding Pi GPIO pins
    - VCC wires → Pi 3.3V rail on breadboard
    - GND bus → breadboard GND rail
    - PAM8403 wires → appropriate breadboard rows

17. **Label the outside** — mark each connector on the box exterior with a marker:
    - `L` and `R` next to the motor headers
    - `LED` next to the 6-pin header
    - `AUD IN` and `AUD OUT` next to the 3.5mm jacks

**Harness identification:** The two JST-XH 5-pin motor harnesses use identical wire color coding but are distinguished by zip tie color at the connector end:
- **Blue zip tie** = Left motor harness ("L")
- **Yellow zip tie** = Right motor harness ("R")

## Internal Wiring Summary

```
    FACE A (input)                     FACE B (output)
    ┌───────────┐                      ┌────────────────────┐
    │           │                      │                    │
    │  Pi USB ──┼── USB adapter ─┐     │  ◎ OUT ←── PAM8403 │
    │           │   (external)   │     │                    │
    │     ◎ IN ←┼────────────────┘     │  [LED] ←── GPIO   │
    │       │   │                      │  24,25,5,6         │
    │       ▼   │                      │                    │
    │  PAM8403  │                      │  [L 5p] ←── GPIO  │
    │  (bread-  │                      │  17,27,12 + pwr    │
    │   board)  │                      │                    │
    │       │   │                      │  [R 5p] ←── GPIO  │
    │       ▼   │                      │  22,23,13 + pwr    │
    │  routes ──┼──────────────────────┼──→ ◎ OUT           │
    │           │                      │                    │
    └───────────┘                      └────────────────────┘
```

## Testing

After assembly, before installing in the robot:

1. **Continuity check** — use a multimeter to verify each pin on the external JST-XH connectors reaches the correct breadboard row. Check that no adjacent pins are shorted.

2. **Audio loop test** — connect a phone or audio source to the IN jack, connect a speaker to the OUT jack, power the PAM8403 from the Pi 5V pin. Verify sound passes through and the volume pot works.

3. **LED test** — plug in the LED harness, power the Pi, run:
   ```python
   from gpiozero import LED
   from time import sleep
   for pin in [24, 25, 5, 6]:
       led = LED(pin)
       led.on(); sleep(0.5); led.off()
   ```

4. **Motor signal test** — plug in the L and R harnesses (connected to TB6612FNG in the base), power the Pi and battery pack, run:
   ```bash
   EMIGLIO_HARDWARE_MODE=real uv run python scripts/motor_test.py
   ```

## Dependencies

- **Before this guide:** LED harness built (head-wiring.md), motor harnesses built (base-wiring.md)
- **After this guide:** Final assembly — install box in barrel, connect all harnesses, close up robot (HW-10)
