# Video Pipeline

## Stage 1 - Clip generation

`scripts/run_pipeline.py` parses `assets/scripts/episode_001.md` (each `## Scene`
heading becomes a clip). For every scene it sends the scene text + a character
reference image (`assets/characters/*/reference.png`) to OpenRouter
(`x-ai/grok-imagine-video-1.5` by default) and downloads a short mp4 into
`generated/clips/`.

Config: `config/pipeline.yaml` -> `video` section.

## Stage 2 - Voiceover (planned)

TTS synthesis of the script into `generated/voiceover/`.

## Stage 3 - Merge

MoviePy concatenates clips with crossfades, overlays voiceover + music,
and writes the final video to `generated/final/`.

## Adding an episode

1. Write `assets/scripts/episode_00N.md`
2. Add character references under `assets/characters/`
3. Point `config/pipeline.yaml` at the new script
4. `uv run scripts/run_pipeline.py`
