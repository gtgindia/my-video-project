# Video Pipeline

## Stage 0 - Character sheets

`scripts/generate_character_images.py` generates 4 consistent images per
character (reference / portrait / action / profile) with `qwen/qwen-image-3`.
The master `reference.png` is text-to-image (fixed seed); the other poses are
derived from it via `input_references` so face, clothes and colors stay
identical. Output: `assets/characters/<name>/`.

Config: `config/pipeline.yaml` -> `images` + `characters` sections.

## Stage 1 - Clip generation

`scripts/run_pipeline.py` parses `assets/scripts/episode_001.md` (each `## Scene`
heading becomes a clip). For every scene it sends the scene text + the scene
character's `reference.png` to OpenRouter (`x-ai/grok-imagine-video-1.5` by
default) and downloads a short mp4 into `generated/clips/`.

Config: `config/pipeline.yaml` -> `video` section.

## Stage 2 - Music (optional)

`scripts/generate_music.py` generates a background score with
`google/lyria-3-clip-preview` into `generated/music/background_music.mp3`.
Voiceover (TTS) is planned but not implemented yet.

## Stage 3 - Merge

MoviePy concatenates clips with crossfades, mixes background music (looped to
fit, at `music_volume`) and the voiceover (when present, at `voiceover_volume`),
and writes the final video to `generated/final/`.

## Adding an episode

1. Write `assets/scripts/episode_00N.md` (`## Scene` per clip, optional `Character: <name>`)
2. Add the character to `assets/characters/` and `config/pipeline.yaml`
3. `uv run scripts/generate_character_images.py`
4. Point `config/pipeline.yaml` at the new script
5. `uv run scripts/run_pipeline.py`
