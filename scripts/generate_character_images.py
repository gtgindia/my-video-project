"""Generate consistent character reference sheets with qwen/qwen-image-3.

For each character in config/pipeline.yaml:
  1. reference.png  - full body, front view (text-to-image, fixed seed)
  2. portrait.png   - face close-up (derived from reference via input_reference)
  3. action.png     - dynamic pose (derived from reference)

Parallelized in two phases:
  Phase 1 - all masters generated concurrently (they have no dependencies)
  Phase 2 - all chained poses generated concurrently (each depends only on
            its own character's master, which is ready by now)
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from video_pipeline.config import PipelineConfig
from video_pipeline.providers.images import OpenRouterImageClient


def main() -> None:
    cfg = PipelineConfig()
    images = cfg.data["images"]
    client = OpenRouterImageClient(
        model=images["model"],
        resolution=images.get("resolution", "1K"),
        aspect_ratio=images.get("aspect_ratio", "3:4"),
        seed=images.get("seed"),
    )
    prompt_prefix = images.get("prompt_prefix", "")
    poses = images.get("poses", [{"name": "reference", "prompt": "Full body, front view, facing camera"}])
    workers = images.get("max_workers", 3)

    chars = cfg.data["characters"]
    identities: dict[str, str] = {}
    for name, char in chars.items():
        profile = Path(char["description"])
        profile_text = profile.read_text().split("## Prompt style")[0] if profile.exists() else ""
        identities[name] = f"{prompt_prefix}\n{profile_text}".strip()

    def make_pose(name: str, pose_name: str, prompt: str, master_bytes: bytes | None) -> Path:
        char_dir = Path(chars[name]["reference"]).parent
        output = Path(chars[name]["reference"]) if pose_name == "reference" else char_dir / "poses" / f"{pose_name}.png"
        output.parent.mkdir(parents=True, exist_ok=True)
        reference = client.to_data_url(master_bytes) if master_bytes else None
        print(f"[images] {name}: {pose_name}")
        return client.generate_image(prompt, output, reference_url=reference)

    # Phase 1: masters, one per character, in parallel
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(make_pose, name, "reference", poses[0]["prompt"], None): name
            for name in chars
        }
        masters = {}
        for fut in futures:
            masters[futures[fut]] = fut.result().read_bytes()

    # Phase 2: chained poses, all characters/poses in parallel
    with ThreadPoolExecutor(max_workers=workers) as ex:
        tasks = [
            (name, pose["name"], pose["prompt"], masters[name])
            for name in chars
            for pose in poses[1:]
        ]
        list(ex.map(lambda t: make_pose(*t), tasks))

    print("Done. Character sheets in assets/characters/<name>/")


if __name__ == "__main__":
    main()
