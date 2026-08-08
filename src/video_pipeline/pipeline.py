"""Pipeline orchestrator: script -> clips -> voiceover -> merged video."""

from __future__ import annotations

from pathlib import Path

from .config import PipelineConfig
from .providers.minimax import MiniMaxClient


def run_pipeline(cfg: PipelineConfig) -> Path:
    """End-to-end run. Each stage writes to generated/ so it can be re-run."""
    clips_dir = cfg.dir_for("clips")
    voiceover_dir = cfg.dir_for("voiceover")
    final_dir = cfg.dir_for("final")

    client = MiniMaxClient(cfg.minimax["base_url"], cfg.minimax["model"])
    print(f"[stage 0] provider: {cfg.minimax['provider']} (model {cfg.minimax['model']})")

    # Stage 1: generate one clip per scene (parse from script)
    scenes = parse_scenes(cfg.data["episode"]["script"])
    clips: list[Path] = []
    for i, scene in enumerate(scenes):
        image = pick_reference_image(scene, cfg)
        print(f"[stage 1] generating clip {i + 1}/{len(scenes)}")
        clips.append(client.generate_clip(scene.prompt, image, clips_dir))

    # Stage 2: voiceover for the full script
    # from .audio.tts import synthesize
    # voiceover = synthesize(cfg, script_text, voiceover_dir)

    # Stage 3: merge
    from .editing.merge import merge_clips

    final = final_dir / f"{cfg.data['episode']['title'].replace(' ', '_')}.mp4"
    print(f"[stage 3] merging {len(clips)} clips")
    merge_clips(clips, final, **cfg.editing)
    return final


class Scene:
    def __init__(self, prompt: str, character: str | None = None) -> None:
        self.prompt = prompt
        self.character = character


def parse_scenes(script_path: str | Path) -> list[Scene]:
    """Very simple parser: each '## Scene' heading starts a new scene."""
    text = Path(script_path).read_text()
    scenes: list[Scene] = []
    current: list[str] | None = None
    for line in text.splitlines():
        if line.startswith("## Scene"):
            if current is not None and any(l.strip() for l in current):
                scenes.append(Scene("\n".join(current)))
            current = []
        elif current is not None:
            current.append(line)
    if current is not None and any(l.strip() for l in current):
        scenes.append(Scene("\n".join(current)))
    return scenes


def pick_reference_image(scene: Scene, cfg: PipelineConfig) -> Path:
    """Character reference image for the scene, falling back to a default."""
    if scene.character and scene.character in cfg.data["characters"]:
        return Path(cfg.data["characters"][scene.character]["reference"])
    return Path(cfg.data["characters"]["hero"]["reference"])
