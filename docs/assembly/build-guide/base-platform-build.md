# Base Platform Build Guide

**Goal:** Turn the existing Emiglio base into a working, laptop-controllable moving platform.

**End state:** You open `http://<pi-ip>:8080` on your laptop, drag the joystick, and the robot drives around the floor.

## What You're Working With

The base already has:
- **Two DC motors** with gearboxes driving the main wheels (differential drive)
- **Two D-cell battery cases** (4 D batteries total) — original motor power
- **A 12V DC input port** — original wall adapter input
- **Stabilizer wheels** (casters) front and rear
- **Red/black motor wires** (clipped during disassembly — stubs remain on motor terminals)

The software already has:
- **Web UI with joystick** at `http://<host>:8080` — 2D touch/mouse control
- **WebSocket motor control** — joystick sends x/y at 100ms, server maps to left/right motor speeds
- **Virtual robot simulator** — visual feedback with wheel colors, speed gauges, trail
- **Stop button** — emergency halt
- **Event bus wiring** — joystick → WebSocket → EventBus → LocomotionController → MotorDriver → GPIO
- **Mock mode** — `EMIGLIO_HARDWARE_MODE=mock` logs motor commands (for dev without hardware)
- **Motor test script** — `scripts/motor_test.py` runs a predefined sequence

**What you need to add:** A TB6612FNG motor driver board between the Pi's GPIO and the motors.

## Parts Needed

| Item | Have it? | Notes |
|------|----------|-------|
| Raspberry Pi 5 (4GB) | On order | The brains — runs emiglio service |
| TB6612FNG breakout board | To buy | Dual H-bridge motor driver, ~$5-10 |
| 4x D batteries | To buy/have | For the existing battery cases |
| Jumper wires (M-F and M-M) | Elegoo kit | GPIO header to TB6612FNG |
| USB-C power supply (5V 3A+) | To buy/have | Powers the Pi |
| Soldering iron + solder | Have | For motor wire prep |
| Multimeter | Have | For voltage/continuity checks |
| Small screwdriver | Have | To open the base |

## Step-by-Step Build

---

### Step 1: Open the base and survey the internals

**Time:** 10 minutes

1. Flip the base upside down
2. Remove the bottom panel screws (Phillips)
3. Photograph the interior before touching anything — you'll want this for reference
4. Identify and label:
   - Left motor and right motor (when looking from the rear of the robot)
   - Motor wire stubs (red/black on each motor)
   - Battery case wiring
   - The 12V DC input port and where its wires go
   - Any original circuit board remnants

**Record these measurements:**
- Motor wire stub lengths (mm remaining)
- Battery case wiring: are the two cases wired in series (6V) or parallel (3V)?
- Available space for the TB6612FNG board

> **Tip:** The two D-cell cases could be wired various ways. Trace the wires:
> - 2 cases in series = 6V (more likely for driving motors)
> - 2 cases in parallel = 3V with double capacity
> - Each case may itself be 2 cells in series = 3V per case
> Check with a multimeter: load 4 D cells, measure voltage at the output leads.

---

### Step 2: Characterize the motors

**Time:** 15 minutes

You need to know the motor voltage and current draw before wiring the TB6612FNG.

1. **Load the battery cases with 4 D cells**
2. **Measure the battery output voltage** with a multimeter — should be ~6V (4x 1.5V in series) or ~3V
3. **Touch the battery leads directly to one motor** (briefly, 1-2 seconds):
   - Does it spin? Which direction?
   - Does it spin the wheel?
   - Does it sound healthy (smooth hum, not grinding)?
4. **Repeat for the other motor**
5. **If you have a bench supply or the original 12V adapter**, try that too — note how the motors respond at different voltages. This tells you their comfortable operating range.
6. **Measure stall current** (optional but useful): hold the wheel still while powered and read amps. The TB6612FNG handles 1.2A continuous / 3.2A peak per channel.

**Record:**
- Battery voltage: ____V
- Left motor: spins? direction? sounds ok?
- Right motor: spins? direction? sounds ok?
- Stall current (if measured): ____A

> **If stall current exceeds 1.2A:** You'll want an L298N driver instead of TB6612FNG, or cap PWM duty cycle in software to limit current. The TB6612FNG has thermal shutdown protection, so it won't burn out — it'll just cut off.

---

### Step 3: Assess the 12V DC port

**Time:** 5 minutes

Trace where the 12V port wires go:
- If they connect to the battery cases in parallel (as an alternative power source), you can reuse this port to power the motors from a bench supply during development
- If they went to the original circuit board (now removed), you can repurpose the port freely

**Decision point:** For v1.0, you can either:
- **Use the D-cell batteries** (simple, portable, already there)
- **Use a 12V wall adapter through the existing port** (unlimited runtime for bench testing)
- **Both** — wire the 12V port and battery cases to the TB6612FNG VM pin through a simple selector (or just swap cables)

> **Recommendation:** Start with D cells for simplicity. Once you've confirmed everything works, add the 12V adapter option for extended testing sessions.

---

### Step 4: Prepare the motor wires

**Time:** 15 minutes

Each motor needs two wires reaching the TB6612FNG.

1. **Inspect the wire stubs** on each motor's terminals
2. **If stubs are long enough** (≥30 mm): strip the ends, tin with solder
3. **If stubs are too short**: solder new ~150 mm lengths of 22 AWG stranded wire to each motor terminal
4. **Use different colors or label** left vs. right motor wires (tape flags or heat shrink)
5. **Note polarity**: for each motor, mark which terminal gives "forward" motion (away from the front of the robot) when the + battery lead is applied. This maps to AO1/BO1 on the TB6612FNG.

---

### Step 5: Wire the TB6612FNG

**Time:** 20 minutes

The TB6612FNG is a small breakout board. Here's what connects where:

```
                    TB6612FNG BREAKOUT
               ┌─────────────────────────┐
               │                         │
    Motor L +──┤ AO1              AO2 ├──Motor L -
               │                         │
    Motor R +──┤ BO1              BO2 ├──Motor R -
               │                         │
  Battery + ──┤ VM          VCC ├── Pi 3.3V
               │                         │
  Battery - ──┤ GND         GND ├── Pi GND
               │                         │
   Pi GPIO 17──┤ AIN1       STBY ├── jumper to VCC
   Pi GPIO 27──┤ AIN2             │
   Pi GPIO 12──┤ PWMA             │
               │                         │
   Pi GPIO 22──┤ BIN1             │
   Pi GPIO 23──┤ BIN2             │
   Pi GPIO 13──┤ PWMB             │
               └─────────────────────────┘
```

**Wiring steps:**

1. **Motor outputs:**
   - Left motor + → AO1, Left motor - → AO2
   - Right motor + → BO1, Right motor - → BO2

2. **Motor power:**
   - Battery case + → VM
   - Battery case - → GND (one of the GND pins)

3. **Logic power:**
   - Pi 3.3V → VCC
   - Pi GND → GND (second GND pin — **common ground with battery is essential**)

4. **Standby:**
   - STBY → jumper wire to VCC (ties it HIGH to enable the driver)

5. **Control signals (use jumper wires to Pi GPIO header):**
   - AIN1 ← Pi GPIO 17 (BCM) = physical pin 11
   - AIN2 ← Pi GPIO 27 (BCM) = physical pin 13
   - PWMA ← Pi GPIO 12 (BCM) = physical pin 32
   - BIN1 ← Pi GPIO 22 (BCM) = physical pin 15
   - BIN2 ← Pi GPIO 23 (BCM) = physical pin 16
   - PWMB ← Pi GPIO 13 (BCM) = physical pin 33

> **Tip:** Use female-to-female jumper wires if the TB6612FNG has header pins. Use male-to-female from the TB6612FNG to the Pi's GPIO header.

---

### Step 6: Mount the TB6612FNG in the base

**Time:** 5 minutes

For now, keep it simple:
- Stick the TB6612FNG to an interior wall of the base using double-sided foam tape
- Position it near the motors to keep motor wires short
- Route the signal wires (6 GPIO + VCC + GND) out through the base top toward where the body will sit

Don't overthink mounting at this stage — you'll refine placement after confirming everything works.

---

### Step 7: Set up the Pi

**Time:** 20 minutes (once Pi arrives)

1. **Flash Raspberry Pi OS** (64-bit Lite or Desktop) onto a microSD card
2. **Enable SSH and WiFi** during flashing (use Raspberry Pi Imager's settings)
3. **Boot the Pi**, SSH in from your laptop
4. **Run the setup script:**
   ```bash
   git clone <your-repo-url> ~/emiglio-robot
   cd ~/emiglio-robot
   bash deploy/setup-pi.sh
   ```
   This installs Python, uv, dependencies, and tests in mock mode.

5. **Connect GPIO wires** from the TB6612FNG to the Pi header per Step 5
6. **Connect Pi power** via USB-C (route cable out through the base or body)

---

### Step 8: Smoke test with motor_test.py

**Time:** 5 minutes

This runs a scripted sequence (forward, backward, turn left, turn right, etc.) to verify all wiring.

```bash
# SSH into Pi, then:
cd ~/emiglio-robot
EMIGLIO_HARDWARE_MODE=real uv run python scripts/motor_test.py
```

**Watch for:**
- Both motors should spin during each test
- "Forward" should drive both wheels the same direction
- "Turn left" should spin wheels in opposite directions
- No grinding, no burning smell, no TB6612FNG getting hot

**If a motor spins the wrong way:** Swap its AO1/AO2 (or BO1/BO2) wires at the TB6612FNG.

**If nothing happens:**
- Check STBY is tied to VCC
- Check battery voltage at VM pin with multimeter
- Check Pi GND is connected to TB6612FNG GND (common ground)
- Check GPIO pin numbers are correct (BCM, not physical)

---

### Step 9: Launch the full emiglio service

**Time:** 2 minutes

```bash
# On Pi:
EMIGLIO_HARDWARE_MODE=real uv run python -m emiglio
```

You should see log output:
```
INFO: MotorDriver initialized with real GPIO pins
INFO: Uvicorn running on http://0.0.0.0:8080
```

---

### Step 10: Drive from your laptop

**Time:** Immediately

1. **Open a browser on your laptop:** `http://<pi-ip>:8080`
   - Find Pi's IP with `hostname -I` on the Pi
2. **You'll see the Emiglio web UI** with a joystick pad and virtual robot simulator
3. **Drag the joystick** — the robot should move
   - Up = forward (both motors)
   - Down = backward
   - Left/right = differential turning
4. **Hit the Stop button** if anything goes wrong
5. **Watch the simulator** — it shows real-time motor states with colored wheels and speed gauges

**That's it — you have a laptop-controlled moving platform.**

---

## Troubleshooting

| Problem | Check |
|---------|-------|
| Web UI loads but joystick does nothing | Check browser console for WebSocket errors; verify Pi firewall allows port 8080 |
| Motors jitter but don't drive | Battery voltage too low; try fresh D cells or the 12V adapter |
| Robot drives but pulls to one side | One motor is weaker; adjust in software or check wiring |
| TB6612FNG gets very hot | Motor stall current too high; limit PWM duty in config or add current limiting |
| Pi disconnects from WiFi when motors start | Motor noise on power rail; ensure separate power supplies, add a capacitor across VM-GND |
| "Mock motors" in logs even though you set REAL | Check env var: `echo $EMIGLIO_HARDWARE_MODE` — must be exactly `real` |

## Future Improvements

Once the basic platform is working:

- **Add the 12V adapter** through the existing port for unlimited bench testing
- **Migrate to systemd service** — `sudo systemctl start emiglio` for auto-start on boot (see `deploy/emiglio.service`)
- **Tune speed curves** — the joystick-to-motor mapping is linear; you may want exponential curves for fine control
- **Add the body and head** — mount electronics in the barrel, stack the head on top
- **Battery monitoring** — add a voltage divider on an ADC pin to monitor D-cell charge level

## Quick Reference

```
Pi GPIO ─────────────────── TB6612FNG ──── Motor
BCM 17 (pin 11) ────────── AIN1
BCM 27 (pin 13) ────────── AIN2
BCM 12 (pin 32) ────────── PWMA ────────── Left motor
BCM 22 (pin 15) ────────── BIN1
BCM 23 (pin 16) ────────── BIN2
BCM 13 (pin 33) ────────── PWMB ────────── Right motor
3.3V   (pin 1)  ────────── VCC + STBY
GND    (pin 6)  ────────── GND ──┐
                                  ├── common ground
Battery -  ─────────────── GND ──┘
Battery +  ─────────────── VM
```

**Start the service:**
```bash
EMIGLIO_HARDWARE_MODE=real uv run python -m emiglio
```

**Open in browser:**
```
http://<pi-ip>:8080
```
