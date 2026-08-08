"""CLI entrypoints per pipeline stage."""

from video_pipeline.config import PipelineConfig
from video_pipeline.pipeline import run_pipeline


def main() -> None:
    cfg = PipelineConfig()
    final = run_pipeline(cfg)
    print(f"Done: {final}")


if __name__ == "__main__":
    main()
