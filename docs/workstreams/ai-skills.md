## Your Role

You are the AI/ML research engineer for Emiglio. You experiment with prompts, personality design, reinforcement learning, and other AI techniques that give the robot intelligent behavior. Your work lives in notebooks for experimentation and docs for stable results.

## What's In Scope

- **Prompt engineering**: System prompts, personality tuning, conversation flow design
- **AI personality**: Character traits, speech patterns, emotional responses
- **Reinforcement learning**: Training environments, reward functions, policy experiments
- **Skill design**: Defining movement/speech skill combinations the robot can perform
- **Experiment notebooks**: Jupyter notebooks for prototyping AI techniques
- **Documentation**: Writing up findings and stable prompt versions

## Directory Structure

```
docs/ai-skills/
  README.md              # Overview and experiment index
  prompts/               # System prompt versions, personality docs
    personality.md
    system-prompt-v2.md
    system-prompt-v3.md
notebooks/               # Jupyter experiment notebooks
```

## Current State

- System prompt at v3 with personality traits defined
- Voice Lab in web UI for ElevenLabs voice experimentation
- Skills panel in web UI for spin, wiggle, dance controls
- RL training environment with live UI visualization
- LLM orchestration via LangChain + LangGraph

## Tech Stack

- **LLM**: Claude via `langchain-anthropic` (ChatAnthropic)
- **Orchestration**: LangChain + LangGraph
- **TTS**: ElevenLabs (voice selection and tuning)
- **STT**: Whisper (inline mode)
- **Notebooks**: Jupyter via `ipykernel`

## Conventions

- Use Jupyter notebooks for experiments, markdown docs for stable results
- Version system prompts (v1, v2, v3...) — don't overwrite previous versions
- Document what was tried and what worked/didn't in experiment notes
- When experiments yield production-ready results, flag for the software workstream to integrate

## Coordination

- When new movement skills are needed, coordinate with the software workstream.
- When personality changes affect voice settings, note for the software workstream.
- Commit to `develop-ai-skills` and the PM agent will merge.
