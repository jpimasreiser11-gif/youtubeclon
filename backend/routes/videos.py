"""Videos API routes."""
from __future__ import annotations

import shutil
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from ..config import CHANNEL_DIRS, OUTPUT_DIR
from ..database import (
    delete_all_videos,
    delete_video,
    get_channel,
    get_video,
    get_video_count,
    get_videos,
)

router = APIRouter()

SAFE_VIDEO_FIELDS = {"script_path", "audio_path", "video_path", "thumbnail_path", "short_path"}


def _safe_unlink(path_value: str) -> bool:
    if not path_value:
        return False
    p = Path(path_value)
    if not p.is_absolute():
        p = OUTPUT_DIR.parent / p
    p = p.resolve()
    output_root = OUTPUT_DIR.resolve()
    if not str(p).startswith(str(output_root)):
        return False
    if p.exists() and p.is_file():
        p.unlink(missing_ok=True)
        return True
    return False


@router.get("/")
async def list_videos(
    channel: str | None = Query(None, description="Filter by channel slug"),
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List videos with optional filters."""
    channel_db_id = None
    if channel:
        ch = get_channel(channel)
        if not ch:
            raise HTTPException(404, f"Channel '{channel}' not found")
        channel_db_id = ch["id"]
    videos = get_videos(channel_id=channel_db_id, status=status, limit=limit, offset=offset)
    total = get_video_count(channel_id=channel_db_id, status=status)
    return {"total": total, "limit": limit, "offset": offset, "videos": videos}


@router.delete("/purge/all")
async def purge_all_videos():
    """Delete all videos from DB and clear generated output files."""
    videos = get_videos(limit=1000000, offset=0)
    removed_files = 0
    for v in videos:
        for key in SAFE_VIDEO_FIELDS:
            if _safe_unlink(v.get(key, "")):
                removed_files += 1

    reset_dirs = 0
    for channel_dir in CHANNEL_DIRS.values():
        for sub in ["scripts", "audio", "clips", "thumbnails", "videos"]:
            target = channel_dir / sub
            if target.exists():
                shutil.rmtree(target, ignore_errors=True)
            target.mkdir(parents=True, exist_ok=True)
            reset_dirs += 1

    deleted_count = delete_all_videos()
    return {
        "ok": True,
        "deleted_videos": deleted_count,
        "removed_files": removed_files,
        "reset_directories": reset_dirs,
    }


@router.get("/{video_id}")
async def get_video_detail(video_id: int):
    """Get a single video by ID."""
    v = get_video(video_id)
    if not v:
        raise HTTPException(404, f"Video {video_id} not found")
    return v


@router.delete("/{video_id}")
async def delete_video_item(video_id: int):
    """Delete one video entry and local generated artifacts."""
    v = get_video(video_id)
    if not v:
        raise HTTPException(404, f"Video {video_id} not found")

    removed_files = 0
    for key in SAFE_VIDEO_FIELDS:
        if _safe_unlink(v.get(key, "")):
            removed_files += 1

    ok = delete_video(video_id)
    if not ok:
        raise HTTPException(404, f"Video {video_id} not found")
    return {"ok": True, "deleted_video_id": video_id, "removed_files": removed_files}
