"""Provider factory: picks the video client from config."""

from __future__ import annotations

from .openrouter import OpenRouterClient


def get_client(cfg) -> OpenRouterClient:
    provider = cfg.video["provider"]
    if provider == "openrouter":
        return OpenRouterClient(
            model=cfg.video["model"],
            resolution=cfg.video.get("resolution", "720p"),
            aspect_ratio=cfg.video.get("aspect_ratio", "16:9"),
            generate_audio=cfg.video.get("generate_audio", True),
        )
    if provider == "minimax":
        from .minimax import MiniMaxClient

        base_url = cfg.video.get("minimax_base_url") or "https://api.minimax.io/v1"
        return MiniMaxClient(base_url, cfg.video["model"])
    raise ValueError(f"Unknown provider: {provider}")
