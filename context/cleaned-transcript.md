# Emiglio Robot Project - Video Transcript (Cleaned)

Source: `context/show-and-tell.mp4` (~10 minutes)
Transcribed: 2026-02-27 via OpenAI Whisper (base model)

---

## Introduction [0:00 - 0:46]

So this is the start of a project -- a rather ambitious idea, just an experiment, but one that I'm pretty excited about. The idea is one that I've had for a while, since I saw this robot at my favorite local thrift store. It was in the expensive boutique section, so I did pay like $45 for it, but I think it was worth it.

Currently I have it a little bit disassembled, but basically it's just missing an arm. Otherwise that's more or less what it looks like. The head is currently detached and I've done more disassembly internally, but this is basically the idea.

## The Robot [0:46 - 1:26]

It's circa maybe '80s or '90s toy. Oh, actually this is missing the bottom. So this is the base, which -- so you can see it moves around and has eyes that light up. There's also lights inside -- the blue lights, really good.

## Disassembly [1:26 - 2:42]

So, okay, so the head comes off. I've taken it off, that is. I just had to unscrew some screws, and I also undid -- or rather clipped -- a bunch of the wires. So now it comes apart into really three nice parts, three nice pieces.

So there's this body assembly -- oops, let's stick this arm in there. So, okay, more than three pieces, but we'll consider these the three main components right now:

1. **The body and arm assembly**
2. **The bottom wheels and motors** -- moving around. And it's pretty simple here, just two motors to move these wheels independently, and then a couple other wheels for stabilizing.
3. **The head** -- looks like this. I have taken out kind of a cool old circuit board. I might have misplaced it, but that went in the back here. I don't intend to keep that, at least not as part of this project.

## The Vision [3:00 - 3:51]

But I do want to keep these three main components because I think they kind of serve as neat discrete functions of what I want to eventually build, which is **a working robot that moves around my floor and can interact with the world around me and with people in different ways**.

So I want to try and build this as quickly as I can. I've gotten pretty quick at building software these days using all the latest tools, but this will be my first time doing actual robotics work. So I'm being fairly ambitious.

## Architecture / Compartmentalization [3:51 - 5:01]

But I also think that this is a nice first project, for one because I have the materials -- at least some of them. And also, as I said, it's really kind of nicely compartmentalized into these three pieces.

So I think what I'd like to do is work kind of independently on:

### Locomotion Base
Getting something that can just kind of move around this floor.

### Body Compartment (Computing & Power)
And then in here, I think this is kind of a nice compartment that I can put -- you know, something still fits wonderfully. I'm thinking maybe even like an oatmeal canister -- you know, one of those cardboard ones -- and I just stick it in there and I could extract it to see what I need. To keep in here: **the main computing and power supply**. So all of the computational logic.

## Future: Modular Arms [5:01 - 5:38]

And then ultimately -- and this should not be part of the first 1.0 build -- but ultimately, I really like that these sockets for the arms are really easy to imagine swapping out for other components. So just imagine having like a vacuum cleaner or just a more capable robotic arm that we attach to it.

## Head: Sensors & I/O [5:38 - 7:13]

So that's kind of the idea for this -- to have computer and just sort of the main interface be in the body. And then in the head, of course, I want to have the **input and output components**:

- **Camera** (at least one)
- **Speaker** (already has one built in, would like to keep using it)
- **Microphone**

I've got some kind of creative ideas for what to do with the head as well. I'd also like to get it to move around -- get it to swivel. It'd be cool to get it to be able to pivot up and down as well. But that would maybe be more mechanical engineering than I can do right now.

### Arms Detail
Also, these arms -- if you look at this, it's a fairly complex assembly. It's got a few joints and different pieces. I haven't opened this up, but... well, this is on a spring. Open that like that. So you could imagine something that can bend and unbend these arms. Currently, it's not very well lubricated, but I guess it's set up to be sort of set in place.

## The Projector Idea [7:13 - 8:10]

So that's the main assembly. And one more thing I'll say about the head -- and this is kind of what inspired this -- an idea that I would love to do.

Okay, so here's the crazy idea. **I got this projector from Amazon**, and it's real cheap -- it was like 40 bucks. I'm a little disappointed in how cheaply built it is, but I guess I should have expected that. But I did try it out, and it works well enough for basically what I might imagine putting in a robot like this.

I mean, actually, you know, **it fits inside this head too**. So imagine just this yellow part flipping up and this being inside, so that you could have a video screen projected onto a wall. And so this robot could travel around the house and could interact with you and also **show you arbitrary images that a computer could render**.

## Development Approach [8:10 - 9:30]

So that's kind of the setup. And my instructions, I think, would be to sort of set this up as a **multi-worker project**. So I imagine having **different sub-agents that are specialized** and even sub-projects specialized to these different components.

And I'm trying to build this quickly, so I want to use everything that I have on hand.

### Available Hardware
- **Raspberry Pi** -- somewhere, could repurpose for this
- **Chromebox** (from eBay, got a bunch of these) -- would obviously not be on battery, but could just plug it in for now

### Tech Stack Preferences
- **Python**
- **Docker**
- **Linux**
- Open source stack

## Closing [9:30 - 10:00]

Yeah, I can plan to go to a thrift store this weekend, but really I want to get as much of this done as possible using basically this as context. So what I've shown here -- and of course I can do follow-ups as needed -- but this is the idea.

I wonder what will come of it. I'm excited. We're just shy of 10 minutes with context. Okay, I'm going to stop.
