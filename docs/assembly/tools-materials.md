# Tools & Materials

## Tools

### Essential

| Tool | Purpose |
|------|---------|
| Phillips screwdriver set | Disassemble/reassemble head and body |
| Soldering iron + solder | Speaker wires, LED, JST connectors |
| Wire strippers | Preparing cable ends |
| Multimeter | Test speaker impedance, verify continuity, check voltages |
| Hot glue gun + sticks | Mount camera, mic, cable anchors, USB sockets |
| Small pliers / tweezers | Working in tight head cavity |
| Flush cutters | Trimming leads, cutting zip ties |
| Ruler / calipers | Measuring cavities, sockets, openings across all sections |
| Small flat-head screwdriver | Screw terminal connections on base connector |

### Nice to Have

| Tool | Purpose |
|------|---------|
| Dremel / rotary tool | Enlarge eye socket if needed for camera fit |
| Drill + small bits (2-4 mm) | Mic sound hole, ventilation, cable pass-through, power cable hole |
| Hole saw or step drill bit (~10 mm) | Power cable pass-through in barrel rear wall |
| Heat shrink gun / lighter | Insulating solder joints |
| Third-hand / helping hands | Holding parts while soldering |
| Label maker or masking tape + pen | Labeling cables at neck connector |

## Materials / Consumables

### Connectors & Wire

| Item | Qty | Purpose |
|------|-----|---------|
| JST-XH 4-pin connector pair (male + female + crimp pins) | 1 | Neck disconnect for speaker + LED |
| USB 2.0 extension cables (short, ~150 mm) | 2 | Neck disconnect for camera + mic USB |
| 22 AWG stranded wire (red + black) | ~2 m each | Speaker wires, motor wires, ground bus |
| 26 AWG stranded wire (4+ colors) | ~2 m each | LED wires, GPIO signal wires (base-to-body) |
| Heat shrink tubing, assorted sizes | A few pieces | Insulating solder joints |

### Mounting

| Item | Qty | Purpose |
|------|-----|---------|
| Hot glue sticks | Several | General mounting |
| Small zip ties (100 mm) | ~10 | Cable bundling, strain relief |
| Adhesive cable clips | 2-4 | Routing cables inside head/body |
| Double-sided foam tape (thin) | 1 roll | Mounting mic, cushioning camera |
| M2.5 screws + standoffs (10-12 mm) | 4-8 | Mounting Pi 5 and camera board |
| Felt pads (small, adhesive) | 4-6 | Head-to-body friction fit pads |
| Rubber grommet (~10 mm ID) | 1 | Protect USB-C power cable at barrel wall hole |

### Electronics (Head)

| Item | Qty | Purpose |
|------|-----|---------|
| 5mm red LED | 1-2 | Eye glow |
| 220Ω resistor | 1-2 | LED current limiting |
| USB webcam (small / board style) | 1 | Vision |
| USB microphone (dongle or MEMS board) | 1 | Audio input |

### Electronics (Base)

| Item | Qty | Purpose |
|------|-----|---------|
| TB6612FNG motor driver breakout | 1 | Dual H-bridge for 2 DC motors |
| D batteries | 4 | Motor power (existing cases in base) |
| 10-position screw terminal block | 1 | Base-to-body connector (prototyping) |
| Velcro strips (adhesive) | 1 pair | Secure battery holder for easy removal |
| Silicone grease (small tube) | 1 | Gearbox lubrication if noisy |

### Electronics (Body)

| Item | Qty | Purpose |
|------|-----|---------|
| Raspberry Pi 5 (4GB) | 1 | Main computer |
| PAM8403 amplifier board | 1 | Drives speaker from Pi audio out |
| Breadboard (half-size) | 1 | Prototyping connections in body |
| USB-C power supply (5V 3A+) | 1 | Pi power (wall adapter for v1.0) |
| Passive aluminum heat sink (Pi 5) | 1 | Thermal management for Pi SoC |
| 3.5mm aux cable (short, ~150 mm) | 1 | Pi audio out to PAM8403 input |
| Dupont jumper wires (M-M, M-F) | ~20 | GPIO header to breadboard connections |

## What's Already on Hand

Per project overview and Elegoo starter kit:

- [x] Emiglio robot chassis (head, body, base)
- [x] Existing speaker in head (needs testing)
- [x] Existing DC motors in base (needs wire prep)
- [x] D-cell battery cases in base (2 cases, 4 cells total)
- [x] 12V DC input port on base
- [x] LEDs and resistors (Elegoo kit)
- [x] Breadboard and jumper wires (Elegoo kit)
- [ ] Raspberry Pi 5 (on order)
- [ ] TB6612FNG motor driver (to purchase)
- [ ] PAM8403 amplifier (to purchase)
- [ ] D batteries x4 (to purchase — for existing cases in base)
- [ ] USB webcam (to purchase — look for compact/board style)
- [ ] USB microphone (to purchase)
- [ ] JST-XH connectors (to purchase)
- [ ] USB extension cables (to purchase)
- [ ] Screw terminal block, 10-position (to purchase)
- [ ] 22 AWG + 26 AWG stranded wire, assorted colors (to purchase)
- [ ] Velcro strips (to purchase)
- [ ] Passive heat sink for Pi 5 (to purchase)
- [ ] 3.5mm aux cable, short (to purchase)
- [ ] Rubber grommet ~10 mm (to purchase)
- [ ] Oatmeal canister or similar cylinder for body sled (source from pantry or hardware store)
