"""Central config loader for the video pipeline."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


class PipelineConfig:
    def __init__(self, path: Path | str = ROOT / "config" / "pipeline.yaml") -> None:
        self.path = Path(path)
        with self.path.open() as f:
            self.data = yaml.safe_load(f)
        self.minimax = self.data["minimax"]
        self.tts = self.data["tts"]
        self.editing = self.data["editing"]
        self.paths = {k: ROOT / v for k, v in self.data["paths"].items()}

    def dir_for(self, key: str) -> Path:
        self.paths[key].mkdir(parents=True, exist_ok=True)
        return self.paths[key]
