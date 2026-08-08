"""Generate a background music clip with google/lyria-3-clip-preview.

Usage:
  uv run scripts/generate_music.py "cinematic orchestral score, tense and epic"
  uv run scripts/generate_music.py --config        # use prompt from pipeline.yaml
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from video_pipeline.config import PipelineConfig
from video_pipeline.providers.audio import OpenRouterAudioClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate background music with Lyria 3")
    parser.add_argument("prompt", nargs="?", help="music description (defaults to config)")
    parser.add_argument("--config", action="store_true", help="use prompt from config/pipeline.yaml")
    parser.add_argument("--image-url", help="optional reference image URL")
    parser.add_argument("--out", help="output path (default generated/music/)")
    args = parser.parse_args()

    cfg = PipelineConfig()
    music = cfg.data["music"]
    client = OpenRouterAudioClient(model=music["model"], format=music.get("format", "mp3"))

    if args.config or not args.prompt:
        prompt = music["prompt"]
    else:
        prompt = args.prompt

    out_dir = cfg.dir_for("music")
    out_path = Path(args.out) if args.out else out_dir / "background_music"
    print(f"[audio] generating: {prompt[:80]}...")
    client.generate_music(prompt, out_path, image_url=args.image_url or music.get("image_url") or None)


if __name__ == "__main__":
    sys.exit(main())
