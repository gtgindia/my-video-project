"""OpenRouter video generation client (provider: openrouter).

Uses OpenRouter's unified POST /api/v1/videos endpoint. Works with any
OpenRouter video model slug, e.g. x-ai/grok-imagine-video-1.5.
API: https://openrouter.ai/docs/api/api-reference/video-generation
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import urljoin

import httpx
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://openrouter.ai/api/v1"
STATUS_POLL_INTERVAL = 10.0
TERMINAL_FAILURES = {"failed", "cancelled", "expired"}


class OpenRouterError(RuntimeError):
    pass


class OpenRouterClient:
    def __init__(
        self,
        model: str,
        resolution: str = "720p",
        aspect_ratio: str = "16:9",
        generate_audio: bool = True,
    ) -> None:
        self.model = model
        self.resolution = resolution
        self.aspect_ratio = aspect_ratio
        self.generate_audio = generate_audio
        self.api_key = os.environ.get("VIDEO_MODEL_KEY")
        if not self.api_key:
            raise OpenRouterError("VIDEO_MODEL_KEY must be set in .env")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def generate_clip(
        self,
        prompt: str,
        image_path: Path | None,
        output_dir: Path,
        duration_seconds: int = 8,
        frame_image_url: str | None = None,
    ) -> Path:
        """Generate one clip from a prompt (+ optional first-frame image)."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "duration": duration_seconds,
            "resolution": self.resolution,
            "aspect_ratio": self.aspect_ratio,
            "generate_audio": self.generate_audio,
        }
        if frame_image_url:
            image_url = frame_image_url
        elif image_path is not None:
            image_url = self._upload_image(image_path)
        else:
            image_url = None
        if image_url:
            payload["frame_images"] = [
                {
                    "type": "image_url",
                    "image_url": {"url": image_url},
                    "frame_type": "first_frame",
                }
            ]

        resp = httpx.post(f"{API_BASE}/videos", headers=self._headers(), json=payload, timeout=60)
        if resp.status_code == 402:
            raise OpenRouterError("Insufficient OpenRouter credits")
        resp.raise_for_status()

        job = resp.json()
        print(f"[openrouter] submitted job {job['id']} ({job['status']})")
        job = self._poll(job)

        clip_path = output_dir / f"{job['id']}.mp4"
        self._download(job, clip_path)
        return clip_path

    def _upload_image(self, image_path: Path) -> str:
        """Upload a local image and return a URL usable as a first frame.

        Requires a management API key; regular keys get 403. In that case,
        host the image somewhere public (e.g. GitHub raw, imgur) and pass
        its URL via the `frame_image_url` config option instead.
        """
        try:
            with image_path.open("rb") as f:
                resp = httpx.post(
                    f"{API_BASE}/files",
                    headers=self._headers(),
                    files={"file": (image_path.name, f, "image/png")},
                    timeout=120,
                )
            resp.raise_for_status()
            file_id = resp.json()["id"]
            return f"{API_BASE}/files/{file_id}/content"
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                raise OpenRouterError(
                    "File upload requires a management key (403). "
                    f"Host {image_path} at a public HTTPS URL instead and set "
                    "`frame_image_url` in config/pipeline.yaml."
                ) from e
            raise

    def _poll(self, job: dict, timeout: int = 1800) -> dict:
        elapsed = 0
        while elapsed < timeout:
            status = job.get("status")
            if status == "completed":
                return job
            if status in TERMINAL_FAILURES:
                raise OpenRouterError(f"Video job {job.get('id')} {status}: {job.get('error')}")
            time.sleep(STATUS_POLL_INTERVAL)
            elapsed += STATUS_POLL_INTERVAL

            polling_url = job.get("polling_url") or f"/api/v1/videos/{job['id']}"
            resp = httpx.get(
                urljoin("https://openrouter.ai", polling_url),
                headers=self._headers(),
                timeout=30,
            )
            resp.raise_for_status()
            job = resp.json()
            print(f"[openrouter] job {job.get('id')}: {job.get('status')}")
        raise OpenRouterError(f"Video job {job.get('id')} timed out")

    def _download(self, job: dict, dest: Path) -> None:
        video_url = job.get("unsigned_urls", [None])[0]
        headers = None
        if not video_url:
            video_url = f"{API_BASE}/videos/{job['id']}/content?index=0"
            headers = self._headers()
        with httpx.stream("GET", video_url, headers=headers, timeout=300) as r:
            r.raise_for_status()
            with dest.open("wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)
