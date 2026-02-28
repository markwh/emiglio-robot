# Notebooks

Jupyter notebooks for AI/ML experiments and prompt evaluation.

## Setup

```bash
uv sync
uv run jupyter lab
```

Requires an `ANTHROPIC_API_KEY` environment variable for notebooks that call the Claude API.

## Notebooks

| Notebook | Purpose |
|----------|---------|
| [personality_testing.ipynb](personality_testing.ipynb) | Compare v1 vs v2 system prompts across test scenarios |
