"""Pipeline orchestrator: script -> clips -> music -> merged video."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .config import PipelineConfig
from .providers import get_client


def run_pipeline(cfg: PipelineConfig) -> Path:
    """End-to-end run. Each stage writes to generated/ so it can be re-run."""
    clips_dir = cfg.dir_for("clips")
    final_dir = cfg.dir_for("final")

    client = get_client(cfg)
    print(f"[stage 0] provider: {cfg.video['provider']} (model {cfg.video['model']})")
    frame_image_url = cfg.video.get("frame_image_url") or None
    workers = cfg.video.get("max_workers", 3)

    # Stage 1: submit one clip per scene, then wait for all in parallel
    scenes = parse_scenes(cfg.data["episode"]["script"])
    submitted = [
        client.submit_clip(
            scene.prompt,
            pick_reference_image(scene, cfg),
            clips_dir,
            duration_seconds=cfg.video["duration_seconds"],
            frame_image_url=frame_image_url,
        )
        for scene in scenes
    ]
    print(f"[stage 1] submitted {len(submitted)} clips, waiting...")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        clips = list(ex.map(lambda job_path: client.wait_for_clip(*job_path), submitted))

    # Stage 2: voiceover for the full script
    # from .audio.tts import synthesize
    # voiceover = synthesize(cfg, script_text, voiceover_dir)

    # Stage 3: merge
    from .editing.merge import merge_clips

    final = final_dir / f"{cfg.data['episode']['title'].replace(' ', '_')}.mp4"
    print(f"[stage 3] merging {len(clips)} clips")
    music_path = cfg.paths["music"] / f"background_music.{cfg.data['music']['format']}"
    music_enabled = cfg.data["music"].get("enabled", False)
    merge_clips(
        clips,
        final,
        transition=cfg.editing["transition"],
        transition_duration=cfg.editing["transition_duration"],
        voiceover_path=None,  # wired in when stage 2 (TTS) is implemented
        music_path=music_path if music_enabled and music_path.exists() else None,
        voiceover_volume=cfg.editing["voiceover_volume"],
        music_volume=cfg.editing["music_volume"],
    )
    return final


class Scene:
    def __init__(self, prompt: str, character: str | None = None) -> None:
        self.prompt = prompt
        self.character = character


def parse_scenes(script_path: str | Path) -> list[Scene]:
    """Very simple parser: each '## Scene' heading starts a new scene.
    A 'Character: <name>' line sets the scene's character."""
    text = Path(script_path).read_text()
    scenes: list[Scene] = []
    current: list[str] | None = None
    character: str | None = None
    for line in text.splitlines():
        if line.startswith("## Scene"):
            if current is not None and any(l.strip() for l in current):
                scenes.append(Scene("\n".join(current), character))
            current = []
            character = None
        elif current is not None and line.strip().lower().startswith("character:"):
            character = line.split(":", 1)[1].strip()
        elif current is not None:
            current.append(line)
    if current is not None and any(l.strip() for l in current):
        scenes.append(Scene("\n".join(current), character))
    return scenes


def pick_reference_image(scene: Scene, cfg: PipelineConfig) -> Path:
    """Character reference image for the scene, falling back to the first configured character."""
    chars = cfg.data["characters"]
    if scene.character and scene.character in chars:
        return Path(chars[scene.character]["reference"])
    return Path(next(iter(chars.values()))["reference"])
