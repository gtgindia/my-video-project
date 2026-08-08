"""Clip merging + final render using MoviePy."""

from __future__ import annotations

from pathlib import Path

from moviepy import VideoFileClip, concatenate_videoclips


def merge_clips(
    clip_paths: list[Path],
    output_path: Path,
    transition: str = "crossfade",
    transition_duration: float = 0.5,
    audio_path: Path | None = None,
) -> Path:
    """Concatenate clips into one video, optionally layering voiceover audio."""
    clips = [VideoFileClip(str(p)) for p in clip_paths]

    if len(clips) == 1:
        merged = clips[0]
    elif transition == "crossfade":
        merged = concatenate_videoclips(clips, method="chain", padding=-transition_duration)
    else:
        merged = concatenate_videoclips(clips)

    if audio_path is not None and audio_path.exists():
        merged = merged.with_audio(VideoFileClip(str(audio_path)).audio)

    merged.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
    )
    for c in clips:
        c.close()
    return output_path
