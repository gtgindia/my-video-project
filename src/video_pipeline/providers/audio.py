"""OpenRouter music generation client (provider: openrouter).

Uses the chat/completions endpoint with `modalities: ["text", "audio"]`.
Audio output requires streaming: base64 audio arrives in SSE chunks under
`choices[0].delta.audio.data`.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://openrouter.ai/api/v1"


class OpenRouterAudioError(RuntimeError):
    pass


class OpenRouterAudioClient:
    def __init__(self, model: str = "google/lyria-3-clip-preview", format: str = "mp3") -> None:
        self.model = model
        self.format = format
        self.api_key = os.environ.get("VIDEO_MODEL_KEY")
        if not self.api_key:
            raise OpenRouterAudioError("VIDEO_MODEL_KEY must be set in .env")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def generate_music(
        self,
        prompt: str,
        output_path: Path,
        image_url: str | None = None,
    ) -> Path:
        """Generate a music clip from a text prompt (+ optional image)."""
        content: list[dict] = [{"type": "text", "text": prompt}]
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": image_url}})

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content}],
            "modalities": ["text", "audio"],
            "audio": {"format": self.format},
            "stream": True,
        }

        chunks: list[str] = []
        buffer = ""
        with httpx.stream(
            "POST",
            f"{API_BASE}/chat/completions",
            headers=self._headers(),
            json=payload,
            timeout=600,
        ) as resp:
            if resp.status_code == 402:
                raise OpenRouterAudioError("Insufficient OpenRouter credits")
            resp.raise_for_status()
            for line in resp.iter_lines():
                if not line:
                    continue
                buffer += line + "\n"
                while "\n" in buffer:
                    raw, buffer = buffer.split("\n", 1)
                    raw = raw.strip()
                    if not raw.startswith("data:"):
                        continue
                    data = raw[5:].strip()
                    if data == "[DONE]":
                        break
                    chunk = json.loads(data)
                    audio = chunk.get("choices", [{}])[0].get("delta", {}).get("audio")
                    if audio and audio.get("data"):
                        chunks.append(audio["data"])

        if not chunks:
            raise OpenRouterAudioError("No audio received from model")

        output_path = output_path.with_suffix(f".{self.format}")
        output_path.write_bytes(base64.b64decode("".join(chunks)))
        print(f"[audio] saved {output_path} ({output_path.stat().st_size} bytes)")
        return output_path
