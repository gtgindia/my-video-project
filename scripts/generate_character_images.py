"""Generate consistent character reference sheets with qwen/qwen-image-3.

For each character in config/pipeline.yaml:
  1. reference.png  - full body, front view (text-to-image, fixed seed)
  2. portrait.png   - face close-up (derived from reference via input_reference)
  3. action.png     - dynamic pose (derived from reference)
  4. profile.png    - three-quarter view (derived from reference)

Poses 2-4 use the master reference as an image input, so clothes, colors
and face stay identical across the sheet.
"""

from __future__ import annotations

import base64
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

    for name, char in cfg.data["characters"].items():
        char_dir = Path(char["reference"]).parent
        poses_dir = char_dir / "poses"
        poses_dir.mkdir(parents=True, exist_ok=True)

        profile = Path(char["description"])
        # Use only the visual description sections; skip meta instructions
        # (e.g. the "Prompt style" section meant for video prompts).
        profile_text = profile.read_text().split("## Prompt style")[0] if profile.exists() else ""
        identity = f"{prompt_prefix}\n{profile_text}".strip()

        master_bytes: bytes | None = None
        for pose in poses:
            prompt = f"{identity}\n\nPose: {pose['prompt']}"
            if pose["name"] == "reference":
                output = Path(char["reference"])
            else:
                output = poses_dir / f"{pose['name']}.png"

            print(f"[images] {name}: {pose['name']}")
            reference = None
            if master_bytes is not None:
                reference = client.to_data_url(master_bytes)
            saved = client.generate_image(prompt, output, reference_url=reference)
            if master_bytes is None:
                master_bytes = saved.read_bytes()

    print("Done. Character sheets in assets/characters/<name>/")


if __name__ == "__main__":
    main()
