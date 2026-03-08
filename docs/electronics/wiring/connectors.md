# Connector Interfaces

Emiglio uses detachable connectors between zones so the head and base can be separated for service.

## Base-to-Body Connector (9 wires)

Located at the interface between the base platform and body barrel.

| Wire # | Signal | Direction | Gauge | Color Suggestion |
|--------|--------|-----------|-------|------------------|
| 1 | AIN1 (GPIO 17) | Body -> Base | 26 AWG | White |
| 2 | AIN2 (GPIO 27) | Body -> Base | 26 AWG | Gray |
| 3 | PWMA (GPIO 12) | Body -> Base | 26 AWG | Yellow |
| 4 | BIN1 (GPIO 22) | Body -> Base | 26 AWG | Blue |
| 5 | BIN2 (GPIO 23) | Body -> Base | 26 AWG | Green |
| 6 | PWMB (GPIO 13) | Body -> Base | 26 AWG | Orange |
| 7 | VCC (3.3V) | Body -> Base | 26 AWG | Red |
| 8 | GND (logic) | Body -> Base | 22 AWG | Black |
| 9 | GND (battery) | Base -> Body | 22 AWG | Black |

Wires 8 and 9 can be combined (same GND rail) = 8 wires minimum.

**Prototyping connector**: 10-position screw terminal block (one spare position)
**Final connector**: 10-pin IDC/ribbon or JST-XH 10-pin (keyed, prevents reversed insertion)

## Neck Connector — Head to Body

### JST-XH 4-pin (Speaker + LED)

| Pin | Signal | Color Suggestion |
|-----|--------|------------------|
| 1 | Speaker + | Red |
| 2 | Speaker - | Black |
| 3 | LED signal (via resistor) | White |
| 4 | LED ground | Green |

### USB Pass-Through (Camera + Mic)

Two short USB 2.0 extension cables:

- **CAM**: Female socket hot-glued inside barrel rim, male plug on head-side cable
- **MIC**: Same arrangement, labeled

This gives a fully detachable head: unplug 2x USB + 1x JST = head lifts off.

## Connector Diagram

```
         ┌─── HEAD ────┐
         │  Camera      │───── USB-A male ──┐
         │  Mic         │───── USB-A male ──┤
         │  Speaker+LED │───── JST 4-pin ───┤
         └──────────────┘                   │
                                    ┌───────┴────────┐
                                    │  Neck Interface │
                                    │  (detachable)   │
                                    └───────┬────────┘
         ┌─── BODY ────┐                   │
         │  Pi USB-A    │◄── USB-A female ──┤
         │  Pi USB-A    │◄── USB-A female ──┤
         │  Breadboard  │◄── JST 4-pin ────┘
         │              │
         │  Screw term  │───── 9-wire ──────┐
         └──────────────┘                   │
                                    ┌───────┴────────┐
                                    │ Base Interface  │
                                    │ (detachable)    │
                                    └───────┬────────┘
         ┌─── BASE ────┐                   │
         │  TB6612FNG   │◄── 9-wire ───────┘
         │  Motors      │
         │  Batteries   │
         └──────────────┘
```
