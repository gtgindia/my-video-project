# my-video-project

AI-assisted video production pipeline: script + character images -> short
clips (OpenRouter video models, e.g. x-ai/grok-imagine-video-1.5) -> merged
10-minute video (MoviePy).

## Setup

```bash
uv sync
cp .env.example .env   # add MINIMAX_API_KEY and MINIMAX_GROUP_ID
```

## Run

```bash
uv run scripts/run_pipeline.py
```

## Layout

```
assets/       source material: scripts, characters, storyboards, audio, fonts
config/       pipeline.yaml - every tunable setting
src/          video_pipeline package (providers, audio, editing, pipeline)
scripts/      CLI entrypoints per stage
generated/    pipeline output: clips -> drafts -> final (gitignored)
docs/         pipeline + API notes
tests/        pytest suite
```

See `docs/pipeline.md` for the full pipeline walkthrough.
