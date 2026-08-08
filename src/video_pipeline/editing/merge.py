"""Clip merging + final render using MoviePy."""

from __future__ import annotations

from pathlib import Path

from moviepy import AudioFileClip, VideoFileClip, concatenate_videoclips
from moviepy.audio.AudioClip import CompositeAudioClip


def merge_clips(
    clip_paths: list[Path],
    output_path: Path,
    transition: str = "crossfade",
    transition_duration: float = 0.5,
    voiceover_path: Path | None = None,
    music_path: Path | None = None,
    voiceover_volume: float = 1.0,
    music_volume: float = 0.15,
) -> Path:
    """Concatenate clips, then mix voiceover + background music underneath."""
    clips = [VideoFileClip(str(p)) for p in clip_paths]

    if len(clips) == 1:
        merged = clips[0]
    elif transition == "crossfade":
        merged = concatenate_videoclips(clips, method="chain", padding=-transition_duration)
    else:
        merged = concatenate_videoclips(clips)

    tracks: list[AudioFileClip] = []
    if voiceover_path is not None and voiceover_path.exists():
        tracks.append(AudioFileClip(str(voiceover_path)).with_volume_scaled(voiceover_volume))
    if music_path is not None and music_path.exists():
        music = AudioFileClip(str(music_path)).with_volume_scaled(music_volume)
        if music.duration < merged.duration:
            music = music.loop(duration=merged.duration)
        tracks.append(music)

    if tracks:
        audio = CompositeAudioClip(tracks).with_duration(merged.duration)
        merged = merged.with_audio(audio)

    merged.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac",
    )
    for c in clips:
        c.close()
    return output_path
