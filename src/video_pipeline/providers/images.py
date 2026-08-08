"""OpenRouter image generation client (provider: openrouter).

Uses OpenRouter's POST /api/v1/images endpoint. Returns images as base64.
API: https://openrouter.ai/docs/guides/overview/multimodal/image-generation
"""

from __future__ import annotations

import base64
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://openrouter.ai/api/v1"


class OpenRouterImageError(RuntimeError):
    pass


class OpenRouterImageClient:
    def __init__(
        self,
        model: str = "qwen/qwen-image-3",
        resolution: str = "1K",
        aspect_ratio: str = "3:4",
    ) -> None:
        self.model = model
        self.resolution = resolution
        self.aspect_ratio = aspect_ratio
        self.api_key = os.environ.get("VIDEO_MODEL_KEY")
        if not self.api_key:
            raise OpenRouterImageError("VIDEO_MODEL_KEY must be set in .env")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def generate_image(
        self,
        prompt: str,
        output_path: Path,
        reference_url: str | None = None,
    ) -> Path:
        """Generate one image and save it. Returns the output path."""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "resolution": self.resolution,
            "aspect_ratio": self.aspect_ratio,
        }
        if reference_url:
            payload["input_references"] = [
                {"type": "image_url", "image_url": {"url": reference_url}}
            ]

        resp = httpx.post(f"{API_BASE}/images", headers=self._headers(), json=payload, timeout=180)
        if resp.status_code == 402:
            raise OpenRouterImageError("Insufficient OpenRouter credits")
        resp.raise_for_status()

        result = resp.json()
        if not result.get("data"):
            raise OpenRouterImageError(f"No image in response: {result}")
        image = result["data"][0]

        media_type = image.get("media_type", "image/png")
        extension = media_type.split("/")[-1].split(";")[0]
        if extension == "jpeg":
            extension = "jpg"
        data = base64.b64decode(image["b64_json"])
        output_path = output_path.with_suffix(f".{extension}")
        output_path.write_bytes(data)
        print(f"[images] saved {output_path} ({len(data)} bytes)")
        return output_path
