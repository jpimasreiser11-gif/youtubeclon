from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from backend.database import get_channel, init_db
from backend.pipeline.video_builder import download_broll


def download_footage(
    channel_id: str,
    queries: list[str],
    min_clips: int = 10,
) -> dict[str, Any]:
    """
    Download footage via existing provider chain:
    pexels -> pixabay -> free fallback.
    """
    if not channel_id.strip():
        raise ValueError("channel_id is required")
    if min_clips < 1:
        raise ValueError("min_clips must be >= 1")

    init_db()
    channel = get_channel(channel_id)
    if not channel:
        raise ValueError(f"Channel not found: {channel_id}")

    markers = [q.strip() for q in queries if q and q.strip()]
    clips = download_broll(broll_markers=markers, channel=channel, min_clips=min_clips)
    clip_paths = [str(Path(c)) for c in clips]
    if not clip_paths:
        raise RuntimeError(
            f"No footage downloaded for channel '{channel_id}'. Check provider keys/network."
        )

    return {
        "ok": True,
        "channel_id": channel_id,
        "requested_queries": markers,
        "provider_strategy": ["pexels", "pixabay", "fallback"],
        "clips_downloaded": len(clip_paths),
        "clip_paths": clip_paths,
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Phase-4 footage downloader wrapper")
    parser.add_argument("--channel", required=True, dest="channel_id")
    parser.add_argument("--query", action="append", default=[])
    parser.add_argument("--min-clips", type=int, default=4)
    args = parser.parse_args()
    payload = download_footage(
        channel_id=args.channel_id,
        queries=args.query,
        min_clips=args.min_clips,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

