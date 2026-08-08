"""MiniMax H3 (Hailuo) video generation client.

H3 generates short clips (a few seconds) from an image + text prompt.
See docs: https://platform.minimaxi.com/document/Video%20Generation
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

STATUS_POLL_INTERVAL = 5.0


class MiniMaxError(RuntimeError):
    pass


class MiniMaxClient:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url
        self.model = model
        # Generic key: VIDEO_MODEL_KEY works for OpenRouter, MiniMax, Gemini, Grok, ...
        self.api_key = os.environ.get("VIDEO_MODEL_KEY")
        self.group_id = os.environ.get("MINIMAX_GROUP_ID")
        if not self.api_key:
            raise MiniMaxError("VIDEO_MODEL_KEY must be set in .env")
        if not self.group_id:
            raise MiniMaxError("MINIMAX_GROUP_ID must be set in .env for MiniMax")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def generate_clip(
        self,
        prompt: str,
        image_path: Path,
        output_dir: Path,
        duration_seconds: int = 10,
    ) -> Path:
        """Generate one clip from a reference image + prompt. Returns the mp4 path."""
        with image_path.open("rb") as f:
            image = f.read()
        upload_url = f"{self.base_url}/video_generation/image2video/upload"
        video_url = self._upload(upload_url, image, image_path.name)

        task_url = f"{self.base_url}/video_generation/image2video"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "first_frame_image": video_url,
            "video_ration": "16:9",
            "duration": duration_seconds,
            "callback_url": "",  # we poll instead
        }
        resp = httpx.post(task_url, headers=self._headers(), json=payload, timeout=60)
        resp.raise_for_status()
        task_id = resp.json()["task_id"]

        result_url = self._poll(task_url, task_id)
        clip_path = output_dir / f"{task_id}.mp4"
        self._download(result_url, clip_path)
        return clip_path

    def _upload(self, url: str, data: bytes, filename: str) -> str:
        resp = httpx.post(url, headers=self._headers(), files={"file": (filename, data)}, timeout=120)
        resp.raise_for_status()
        return resp.json()["file"]["url"]

    def _poll(self, task_url: str, task_id: str, timeout: int = 600) -> str:
        url = f"{task_url}?task_id={task_id}"
        elapsed = 0
        while elapsed < timeout:
            resp = httpx.get(url, headers=self._headers(), timeout=30)
            resp.raise_for_status()
            status = resp.json()["status"]
            if status == "Success":
                return resp.json()["file_id"]
            if status == "Failed":
                raise MiniMaxError(f"Task {task_id} failed: {resp.json()}")
            time.sleep(STATUS_POLL_INTERVAL)
            elapsed += STATUS_POLL_INTERVAL
        raise MiniMaxError(f"Task {task_id} timed out")

    def _download(self, file_id: str, dest: Path) -> None:
        url = f"{self.base_url}/files/retrieve?file_id={file_id}"
        with httpx.stream("GET", url, headers=self._headers(), timeout=300) as r:
            r.raise_for_status()
            with dest.open("wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
