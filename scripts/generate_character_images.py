"""Generate character reference images with qwen/qwen-image-3.

Reads each character's profile.md, builds a prompt, and writes the
reference image to the path configured in config/pipeline.yaml.
"""

from __future__ import annotations

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
    )
    prompt_prefix = images.get("prompt_prefix", "")

    for name, char in cfg.data["characters"].items():
        profile = Path(char["description"])
        prompt = f"{prompt_prefix}\n{profile.read_text()}" if profile.exists() else prompt_prefix
        print(f"[images] generating {name}")
        client.generate_image(prompt, Path(char["reference"]))


if __name__ == "__main__":
    main()
