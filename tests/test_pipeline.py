"""Smoke test for config loading and script parsing."""

import inspect
from pathlib import Path

from video_pipeline.config import PipelineConfig
from video_pipeline.editing.merge import merge_clips
from video_pipeline.pipeline import Scene, parse_scenes, pick_reference_image


def test_config_loads() -> None:
    cfg = PipelineConfig()
    assert cfg.video["provider"] == "openrouter"
    assert cfg.video["model"] == "bytedance/seedance-2.0"
    assert cfg.dir_for("final").exists()


def test_parse_scenes() -> None:
    scenes = parse_scenes("assets/scripts/episode_001.md")
    assert len(scenes) == 9
    assert all(s.character == "abhimanyu" for s in scenes)
    assert "anime" in scenes[0].prompt.lower()


def test_pick_reference_image_fallback() -> None:
    cfg = PipelineConfig()
    reference = Path(cfg.data["characters"]["abhimanyu"]["reference"])
    assert pick_reference_image(Scene("x", "abhimanyu"), cfg) == reference
    # Scene without a character falls back to the first configured character
    assert pick_reference_image(Scene("x"), cfg) == reference


def test_merge_clips_accepts_editing_config() -> None:
    """The config editing keys must all be valid merge_clips parameters."""
    from video_pipeline.config import PipelineConfig

    params = set(inspect.signature(merge_clips).parameters)
    cfg = PipelineConfig()
    assert set(cfg.editing) <= params
