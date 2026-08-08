"""Smoke test for config loading and script parsing."""

from video_pipeline.config import PipelineConfig
from video_pipeline.pipeline import parse_scenes


def test_config_loads() -> None:
    cfg = PipelineConfig()
    assert cfg.video["provider"] == "openrouter"
    assert cfg.video["model"] == "x-ai/grok-imagine-video-1.5"
    assert cfg.dir_for("final").exists()


def test_parse_scenes() -> None:
    scenes = parse_scenes("assets/scripts/episode_001.md")
    assert len(scenes) == 3
    assert "hero" in scenes[0].prompt.lower()
