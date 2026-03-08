# Emiglio v1.0 Requirements

The v1.0 milestone is a **working robot that moves, sees, hears, speaks, and holds a conversation** — wall-powered, on flat floors, controlled via web UI. No projector, no battery, no autonomous navigation.

## Acceptance Criteria

v1.0 is **done** when Mark can:

1. Plug in the wall adapter and SSH into the Pi
2. Run `uv run python -m emiglio` (or systemd auto-starts it)
3. Open the web UI on his phone
4. Drive the robot around the room with the joystick
5. Hold a voice conversation (push-to-talk → STT → Brain → TTS → speaker)
6. Ask "what do you see?" and get a camera-aware response
7. The robot responds in Emiglio's personality (retro-optimist, warm, 1-3 sentences)

Everything below supports delivering those seven acceptance tests.

---

## Requirements by Workstream

### Hardware — Assembly (`develop-assembly`)

| ID | Requirement | Status | Blocked By |
|----|-------------|--------|------------|
| HW-01 | Pi 5 mounted in body (canister sled) | not_started | — |
| HW-02 | TB6612FNG wired to Pi GPIO and motors | not_started | — |
| HW-03 | PAM8403 wired to Pi audio out and head speaker | not_started | EL-02 |
| HW-04 | USB webcam mounted in head | not_started | — |
| HW-05 | USB microphone mounted in head | not_started | — |
| HW-06 | LED eye wired to GPIO (BCM pin TBD) | not_started | EL-01 |
| HW-07 | JST-XH neck connector (speaker + LED) | not_started | — |
| HW-08 | Screw terminal base-to-body connector (8-pos) | not_started | — |
| HW-09 | USB-C power cable routed into body | not_started | — |
| HW-10 | Head, body, base fully assembled and closeable | not_started | HW-01 through HW-09 |

### Hardware — Electronics (`develop-electronics`)

| ID | Requirement | Status | Blocked By |
|----|-------------|--------|------------|
| EL-01 | LED GPIO pin assignment finalized | not_started | — |
| EL-02 | PAM8403 power source confirmed (Pi 5V vs separate) | not_started | — |
| EL-03 | Audio output method confirmed (3.5mm for v1.0) | done | — |
| EL-04 | Full integrated circuit schematic | not_started | EL-01, EL-02 |

### Software — Pi-side (`develop-software`)

| ID | Requirement | Status | Blocked By |
|----|-------------|--------|------------|
| SW-01 | Locomotion: differential drive via TB6612FNG + gpiozero | done | — |
| SW-02 | Joystick mixing (web joystick → motor PWM) | done | — |
| SW-03 | Camera: OpenCV capture + MJPEG streaming | done | — |
| SW-04 | Audio capture: mic → WAV buffer | done | — |
| SW-05 | Audio playback: WAV/MP3 → speaker | done | — |
| SW-06 | Web UI: joystick, camera feed, push-to-talk, text chat | done | — |
| SW-07 | Conversation loop: mic → STT → Brain → TTS → speaker | done | — |
| SW-08 | Camera frame sent to brain on "what do you see?" | done | — |
| SW-09 | Brain movement commands executed by locomotion | done | — |
| SW-10 | EventBus wiring: all subsystems connected | done | — |
| SW-11 | Config via env vars (EMIGLIO_* prefix, pydantic-settings) | done | — |
| SW-12 | Mock mode works on laptop (no Pi hardware required) | done | — |
| SW-13 | Pi OS setup + emiglio stack installable via SSH | not_started | — |
| SW-14 | systemd service for auto-start on boot | not_started | SW-13 |
| SW-15 | ALSA/PulseAudio config for Pi 5 audio out | not_started | SW-13 |
| SW-16 | Camera + mic device enumeration on Pi | not_started | SW-13 |

### Software — Server-side (`develop-software`)

| ID | Requirement | Status | Blocked By |
|----|-------------|--------|------------|
| SV-01 | STT service (Whisper) — Docker or inline | done | — |
| SV-02 | TTS service (ElevenLabs) — Docker or inline | done | — |
| SV-03 | Brain service (Claude via LangChain/LangGraph) | done | — |
| SV-04 | Brain tool-calling for movement commands | done | — |
| SV-05 | Brain vision: accepts camera frame, describes scene | done | — |
| SV-06 | All services runnable inline (no Docker required) | done | — |

### AI / Personality (`develop-ai-skills`)

| ID | Requirement | Status | Blocked By |
|----|-------------|--------|------------|
| AI-01 | System prompt: retro-optimist personality | done | — |
| AI-02 | Tool-calling prompt (v3) — movement via LangChain tools | done | — |
| AI-03 | 1-3 sentence response style, no emoji/markdown | done | — |
| AI-04 | Capability boundaries (no internet, no arms, honest) | done | — |
| AI-05 | End-to-end voice personality test on real hardware | not_started | SW-13, HW-10 |

---

## Summary

| Workstream | Done | Not Started | Total |
|------------|------|-------------|-------|
| Assembly (HW-*) | 0 | 10 | 10 |
| Electronics (EL-*) | 1 | 3 | 4 |
| Software — Pi (SW-*) | 12 | 4 | 16 |
| Software — Server (SV-*) | 6 | 0 | 6 |
| AI / Personality (AI-*) | 4 | 1 | 5 |
| **Total** | **23** | **18** | **41** |

All parts are in hand (as of 2026-03-08). The critical path is now **hands-on build work**: bench test → assembly → Pi deployment → integration test. All software and AI work is done in mock mode; the remaining SW items (13-16) and AI-05 are blocked on having a running Pi with peripherals connected.

---

## Explicitly Out of Scope for v1.0

These are captured here so they don't creep in. All are candidates for v2.0+.

| Idea | Notes |
|------|-------|
| Battery power | Wall-powered via USB-C is fine for v1.0 |
| Projector in head | Cool but not MVP — visor stays closed |
| Head swivel/tilt | Mechanically complex, deferred |
| Modular arm attachments | No arms for v1.0 (Emiglio acknowledges this in personality) |
| Autonomous navigation | Joystick-driven only for v1.0 |
| Wake word detection | Push-to-talk is sufficient |
| Conversation memory | Stateless conversations are fine for v1.0 |
| Emotion/sentiment detection | Future AI skill |
| Vision prompt templates | Brain handles vision ad hoc for now |
| I2S DAC audio upgrade | 3.5mm jack is good enough |
| LED eye animations | Static LED on/off is fine |
| OLED display | No display for v1.0 |
| NeoPixel LED strips | No decorative lighting |
| Multiple camera angles | One webcam |
| Obstacle avoidance | No sensors beyond camera |

---

## v2.0+ Parking Lot

Capture ideas here as they come. Prioritization happens after v1.0 ships.

| Idea | Category | Complexity | Notes |
|------|----------|------------|-------|
| Battery power (LiPo or USB power bank in body) | hardware | medium | Eliminates wall tether, enables roaming |
| Projector display (visor flips up, projects on walls) | hardware | medium | $40 projector already purchased, fits in head |
| Head swivel servo (pan camera/speaker direction) | hardware | hard | Mechanical design needed for neck joint |
| Modular arm sockets (vacuum, gripper, etc.) | hardware | hard | One arm missing — design both from scratch |
| Autonomous navigation (SLAM or simple wander) | software+AI | hard | Needs obstacle detection strategy |
| Wake word detection ("Hey Emiglio") | software | medium | Always-listening mode, VAD tuning |
| Conversation memory (session + long-term) | AI | medium | LangGraph checkpointing or vector store |
| Emotion detection from voice tone | AI | medium | Sentiment analysis on audio features |
| Vision prompt templates (scene descriptions) | AI | easy | Structured prompts for different visual contexts |
| Scheduled behaviors (patrol, greet, announce) | software+AI | medium | Cron-like task runner + personality routines |
| Multi-room awareness (room identification) | AI+hardware | hard | Needs landmarks or indoor positioning |
| I2S DAC audio upgrade | electronics | easy | Better audio quality, replaces 3.5mm PWM |
| LED eye animations (blink, pulse, express emotion) | software+electronics | easy | PWM control, personality integration |
| NeoPixel accent lighting | electronics | easy | Mood lighting, status indicators |
| OLED status display (on body) | electronics+software | easy | Show status, IP address, mood |
| Web UI v2 (settings, personality tuning, logs) | software | medium | Admin panel beyond basic controls |
| OTA updates (deploy new code without SSH) | software | medium | Git pull + restart via web UI or API |
| Sound effects library (beeps, boops, reactions) | AI+software | easy | Retro robot sounds for personality |
| Object recognition (identify specific items) | AI | medium | Fine-tuned vision or prompt engineering |
| Person recognition (identify household members) | AI | hard | Face embeddings, privacy considerations |
| Voice cloning (custom Emiglio voice) | AI | medium | ElevenLabs voice design or local model |
| Home Assistant integration | software | medium | Control smart home devices via conversation |

---

## Parts Procurement Checklist

All parts received as of 2026-03-08.

| Item | Est. Cost | Status |
|------|-----------|--------|
| Raspberry Pi 5 (4GB) | $60 | received |
| TB6612FNG motor driver | $6 | received |
| PAM8403 mini amplifier | $3 | received |
| USB webcam (compact/board) | $15 | received |
| USB microphone (dongle/MEMS) | $10 | received |
| D batteries x4 | $5 | received |
| Dupont jumper wires (M-M, M-F) | $6 | received |
| Half-size breadboard | $4 | received |
| USB-C power supply (5V 3A+) | $15 | received |
| Passive aluminum heat sink (Pi 5) | $5 | received |
| 3.5mm aux cable (short, ~150mm) | $3 | received |
| JST-XH 4-pin connector pair | $2 | received |
| USB extension cables (short) x2 | $5 | received |
| 10-pos screw terminal block | $3 | received |
| 22 AWG stranded wire (red+black) | $5 | received |
| 26 AWG stranded wire (4 colors) | $5 | received |
| Heat shrink tubing assorted | $3 | received |
| M2.5 screws + standoffs | $4 | received |
| Rubber grommet ~10mm | $2 | received |
| Zip ties, foam tape, cable clips | $5 | received |
| Velcro strips (adhesive) | $3 | received |
| **Total** | **~$170** | **All received** |
