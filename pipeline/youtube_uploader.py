from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from backend.database import get_channel, init_db
from backend.pipeline.publisher import publish_video


def upload_to_youtube(
    channel_id: str,
    video_path: str | Path,
    thumbnail_path: str | Path,
    metadata: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """OAuth upload wrapper over backend.pipeline.publisher.publish_video."""
    init_db()
    channel = get_channel(channel_id)
    if not channel:
        raise ValueError(f"Channel not found: {channel_id}")

    video = Path(video_path)
    thumbnail = Path(thumbnail_path)
    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video}")
    if not thumbnail.exists():
        raise FileNotFoundError(f"Thumbnail not found: {thumbnail}")
    if not metadata.get("title"):
        raise ValueError("metadata.title is required")

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "channel_id": channel_id,
            "video_path": str(video),
            "thumbnail_path": str(thumbnail),
            "metadata_keys": sorted(metadata.keys()),
        }

    youtube_url = publish_video(
        video_path=video,
        thumbnail_path=thumbnail,
        metadata=metadata,
        channel=channel,
    )
    return {"ok": True, "dry_run": False, "channel_id": channel_id, "youtube_url": youtube_url}


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Phase-4 YouTube uploader wrapper")
    parser.add_argument("--channel", required=True, dest="channel_id")
    parser.add_argument("--video", required=True)
    parser.add_argument("--thumbnail", required=True)
    parser.add_argument("--metadata-json", required=True, help="Path to metadata json file")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    metadata = json.loads(Path(args.metadata_json).read_text(encoding="utf-8"))
    payload = upload_to_youtube(
        channel_id=args.channel_id,
        video_path=args.video,
        thumbnail_path=args.thumbnail,
        metadata=metadata,
        dry_run=args.dry_run,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

