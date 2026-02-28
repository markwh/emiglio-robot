# Emiglio Robot Project - Overview

## What Is This?

A project to convert a vintage **Emiglio robot** (GP Toys, ~1980s-90s) into a functional, AI-powered home robot. The robot was purchased for $45 at a thrift store. It is currently partially disassembled and missing one arm.

## Goal

Build a working robot that:
- Moves around the floor autonomously
- Interacts with people (voice, camera, projected display)
- Can be extended with modular attachments

## Physical Architecture

The robot naturally separates into three main components:

### 1. Locomotion Base (Black Platform)
- **GP Toys branded** black plastic base
- **Two DC motors** driving wheels independently (differential drive)
- Additional stabilizer wheels
- Simple, functional drive system already in place

### 2. Body (White Barrel)
- Cylindrical white plastic body with colorful panel stickers
- Open top (rim where head sits)
- **Arm sockets** on both sides (currently one arm attached, one missing)
- Arms have spring-loaded joints with multiple degrees of freedom
- **Planned use**: House the main computer and power supply
  - Idea: Use an oatmeal canister as an internal compartment that can be extracted for maintenance

### 3. Head (Dome with Visor)
- Black dome/visor with head handle on top
- Red LED inside (eye)
- Built-in speaker (to be retained)
- **Planned use**: Sensors and I/O
  - Camera (at least one)
  - Microphone
  - Speaker (existing)
  - **Projector** (key idea -- see below)
  - Head swivel (desired but mechanically challenging)

## The Projector Idea

A small ~$40 projector from Amazon fits inside the robot's head. The concept: the dome's visor flips up, revealing the projector lens, which can project images/video onto walls. This gives the robot an arbitrary visual display capability without needing an attached screen.

## Available Hardware

| Component | Source | Notes |
|-----------|--------|-------|
| Emiglio robot body | Thrift store ($45) | Missing one arm, disassembled |
| Mini projector | Amazon (~$40) | Cheap but functional, fits in head |
| Raspberry Pi | On hand | Could be main computer |
| Chromebox | eBay (multiple) | More powerful option, needs wall power |

## Tech Stack

- **Python** (primary language)
- **Docker** (containerization)
- **Linux** (OS)
- Open source tools throughout

## Development Approach

- **Multi-worker / sub-agent architecture** -- different specialized agents/sub-projects for each component
- Build quickly, using materials on hand
- First-time robotics project (experienced in software)

## Version Roadmap

### v1.0 (MVP)
- [ ] Locomotion: Robot moves around the floor
- [ ] Computing: Main computer housed in body
- [ ] Head I/O: Camera, microphone, speaker working
- [ ] Basic interaction capability

### v2.0+ (Future)
- [ ] Projector integrated in head
- [ ] Head swivel/tilt mechanism
- [ ] Modular arm attachments (vacuum, robotic arm, etc.)
- [ ] Battery power (currently wall-powered is acceptable)
- [ ] Autonomous navigation
