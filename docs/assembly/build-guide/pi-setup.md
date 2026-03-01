# Raspberry Pi 5 Setup Guide

A first-timer walkthrough: from unboxing to running the Emiglio web UI on your local network.

## What You Need

| Item | Notes |
|------|-------|
| Raspberry Pi 5 (4GB) | The board itself |
| USB-C power supply (5V 3A+ / 5V 5A recommended) | The Pi 5 is power-hungry — use a good supply. The official Pi 5 PSU is ideal. A laptop charger may work if it's USB-C PD capable. |
| MicroSD card (16 GB+) | 32 GB recommended. Speed matters — get a Class 10 / A2 card if possible. |
| MicroSD card reader | To flash the OS from your laptop |
| Ethernet cable OR WiFi credentials | For network access. Ethernet is easier for first setup. |
| Your laptop | For flashing, SSH, and browsing the web UI |

**Optional but helpful:**
- Micro-HDMI to HDMI cable + monitor + USB keyboard — for debugging if SSH doesn't work. You probably won't need this if you configure WiFi during flashing.
- Heat sink — stick one on now if you have it; the Pi 5 runs warm.

## Step 1: Flash the OS

You'll write Raspberry Pi OS onto the microSD card from your laptop.

### Install Raspberry Pi Imager

```bash
# Ubuntu/Debian:
sudo apt install rpi-imager

# Or download from: https://www.raspberrypi.com/software/
```

### Flash the card

1. Insert the microSD card into your laptop's card reader
2. Open **Raspberry Pi Imager**
3. Click **Choose Device** → select **Raspberry Pi 5**
4. Click **Choose OS** → select **Raspberry Pi OS (64-bit)** (the default full version is fine; Lite works too if you don't want a desktop)
5. Click **Choose Storage** → select your microSD card
6. **Before clicking Write**, click the **gear icon** (or "Edit Settings") — this is where you configure everything so the Pi is ready to go on first boot:

#### Settings to configure:

| Setting | Value |
|---------|-------|
| **Set hostname** | `emiglio` (so you can find it on the network as `emiglio.local`) |
| **Enable SSH** | Yes — select "Use password authentication" |
| **Set username and password** | Username: `mark` (or whatever you prefer). Set a password you'll remember. |
| **Configure wireless LAN** | Enter your WiFi network name (SSID) and password. Select your country. |
| **Set locale settings** | Your timezone and keyboard layout |

7. Click **Save**, then **Write**. Confirm when prompted. This takes a few minutes.

## Step 2: First boot

1. Remove the microSD card from your laptop
2. Insert it into the Pi 5's microSD slot (on the bottom of the board)
3. If you have an ethernet cable, plug it in now (more reliable than WiFi for first setup)
4. Plug in the USB-C power supply — the Pi boots automatically

**Wait ~60-90 seconds** for the first boot to complete. The Pi will:
- Expand the filesystem
- Connect to WiFi (or ethernet)
- Start the SSH server

## Step 3: Find the Pi on your network

From your laptop:

```bash
# Try the hostname you set:
ping emiglio.local

# If that doesn't resolve, find it by scanning:
# Option A: arp scan (if you have it)
arp -a | grep -i "raspberry\|dc:a6\|d8:3a\|2c:cf"

# Option B: nmap scan of your local subnet
nmap -sn 192.168.1.0/24    # adjust to your subnet
```

If you're on ethernet, your router's admin page usually shows connected devices with their IPs.

## Step 4: SSH in

```bash
ssh mark@emiglio.local
# (use the username and password you set in the imager)
```

You should see a terminal prompt on the Pi. You're in.

**If SSH fails:**
- Wait another minute — the Pi may still be booting
- Check that your laptop and Pi are on the same network
- Plug in a monitor and keyboard to debug (micro-HDMI port on the Pi)

## Step 5: Update the system

First boot is a good time to update everything:

```bash
sudo apt update && sudo apt upgrade -y
```

This can take 5-10 minutes. Let it finish.

## Step 6: Clone the repo and run the setup script

```bash
# Clone the emiglio repo
git clone https://github.com/YOUR_USERNAME/emiglio-robot.git ~/emiglio-robot

# Run the setup script
cd ~/emiglio-robot
bash deploy/setup-pi.sh
```

The setup script installs:
- Python 3 + dev headers
- PortAudio (for audio capture)
- OpenCV (for camera)
- uv (Python package manager)
- All Python dependencies via `uv sync`
- The systemd service file

It also runs a quick smoke test in mock mode at the end.

## Step 7: Test the web UI

Start the emiglio service in mock mode:

```bash
cd ~/emiglio-robot
uv run python -m emiglio
```

You should see:

```
INFO:     MotorDriver running in MOCK mode
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

Now open a browser on your laptop and go to:

```
http://emiglio.local:8080
```

You should see the Emiglio web UI with:
- A joystick control pad
- A virtual robot simulator
- A stop button
- Voice/text input area

**Drag the joystick** — back in the Pi's terminal, you'll see mock motor commands being logged:

```
INFO: MOCK motors: left=0.45, right=0.60
INFO: MOCK motors: left=0.45, right=0.60
```

The virtual robot simulator in the browser should also show the robot moving with colored wheels and speed gauges.

**Press Ctrl+C** in the Pi terminal to stop the service.

## Step 8: Test peripherals (optional, if you have them)

### USB camera

Plug in the USB webcam and test:

```bash
cd ~/emiglio-robot
uv run python scripts/camera_test.py
```

This captures a frame and saves a snapshot. If the camera works, you'll also see the MJPEG stream at `http://emiglio.local:8080/stream` when the full service is running.

### USB microphone + speaker

```bash
# Test recording and playback:
uv run python scripts/audio_test.py

# Or test the speaker with ALSA directly:
speaker-test -t wav -c 1
```

### PAM8403 amplifier

If you've wired the PAM8403 on a breadboard:
1. Connect PAM8403 VCC to Pi pin 2 or 4 (5V)
2. Connect PAM8403 GND to Pi pin 6 (GND)
3. Connect Pi 3.5mm jack to PAM8403 input via aux cable
4. Connect PAM8403 output to a speaker

```bash
# Play a test tone:
speaker-test -t sine -f 440 -c 1
```

Adjust the PAM8403 potentiometer for volume.

## Step 9: Prepare for motor hardware

Tomorrow when the TB6612FNG arrives, you'll switch from mock to real mode. The only change is the environment variable:

```bash
EMIGLIO_HARDWARE_MODE=real uv run python -m emiglio
```

Before that, you can verify the GPIO pins are accessible:

```bash
# Install GPIO tools
sudo apt install -y python3-gpiozero

# Quick test (just checks that gpiozero can access the hardware)
python3 -c "from gpiozero import Device; print(f'GPIO ready: {Device.pin_factory}')"
```

## Quick Reference

| Task | Command |
|------|---------|
| SSH in | `ssh mark@emiglio.local` |
| Start emiglio (mock) | `cd ~/emiglio-robot && uv run python -m emiglio` |
| Start emiglio (real motors) | `cd ~/emiglio-robot && EMIGLIO_HARDWARE_MODE=real uv run python -m emiglio` |
| Web UI | `http://emiglio.local:8080` |
| Camera stream | `http://emiglio.local:8080/stream` |
| Run motor test | `EMIGLIO_HARDWARE_MODE=real uv run python scripts/motor_test.py` |
| View service logs | `journalctl -u emiglio -f` |
| Pi IP address | `hostname -I` (run on Pi) |
| Shut down Pi safely | `sudo shutdown -h now` |

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `emiglio.local` doesn't resolve | Use the Pi's IP address directly. Find it with `hostname -I` on the Pi, or check your router's admin page. |
| SSH "connection refused" | Pi may still be booting — wait 60s and retry. Or SSH isn't enabled — reflash with SSH enabled in imager settings. |
| `uv` command not found after setup | Run `source ~/.bashrc` or log out and back in. uv installs to `~/.local/bin`. |
| "No module named emiglio" | Make sure you're in the `~/emiglio-robot` directory and ran `uv sync`. |
| Web UI loads but no joystick response | Check browser developer console (F12) for WebSocket errors. The Pi firewall may be blocking port 8080 — run `sudo ufw allow 8080` if ufw is active. |
| GPIO permission denied | Add your user to the gpio group: `sudo usermod -aG gpio mark` then log out/in. |
| Pi won't boot (no green LED activity) | Check that the microSD card is fully seated. Try reflashing. |
| Pi boots but no network | Connect a monitor + keyboard to debug. Check WiFi credentials in `raspi-config`. |
