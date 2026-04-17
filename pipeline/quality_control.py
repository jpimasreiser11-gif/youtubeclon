from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def _ffprobe_json(path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=index,codec_type,width,height",
        "-of",
        "json",
        str(path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {result.stderr[:300]}")
    return json.loads(result.stdout or "{}")


def run_quality_checks(
    video_path: str | Path,
    metadata: dict[str, Any],
    thumbnail_path: str | Path | None = None,
    subtitles_path: str | Path | None = None,
    min_duration: float = 30.0,
    max_duration: float = 3600.0,
    min_width: int = 1280,
    min_height: int = 720,
) -> dict[str, Any]:
    """Run 7 pre-upload checks with explicit pass/fail state."""
    video = Path(video_path)
    thumbnail = Path(thumbnail_path) if thumbnail_path else None
    subtitles = Path(subtitles_path) if subtitles_path else None

    checks: list[dict[str, Any]] = []

    exists_ok = video.exists() and video.is_file() and video.stat().st_size > 0
    checks.append({"check": "file_existence", "ok": exists_ok, "details": str(video)})
    if not exists_ok:
        return {"ok": False, "checks": checks, "error": f"Video file missing or empty: {video}"}

    probe = _ffprobe_json(video)
    duration = float((probe.get("format") or {}).get("duration") or 0.0)
    duration_ok = min_duration <= duration <= max_duration
    checks.append(
        {"check": "duration_bounds", "ok": duration_ok, "details": {"duration": duration, "min": min_duration, "max": max_duration}}
    )

    vstreams = [s for s in probe.get("streams", []) if s.get("codec_type") == "video"]
    width = int((vstreams[0] if vstreams else {}).get("width") or 0)
    height = int((vstreams[0] if vstreams else {}).get("height") or 0)
    res_ok = width >= min_width and height >= min_height
    checks.append(
        {"check": "resolution", "ok": res_ok, "details": {"width": width, "height": height, "min_width": min_width, "min_height": min_height}}
    )

    has_audio = any(s.get("codec_type") == "audio" for s in probe.get("streams", []))
    checks.append({"check": "audio_presence", "ok": has_audio, "details": {"audio_stream": has_audio}})

    if subtitles is None:
        # Subtitles can be burned into final render and not persisted as external SRT.
        subtitle_ok = True
        subtitle_details: Any = "embedded_or_not_provided"
    else:
        subtitle_ok = subtitles.exists() and subtitles.stat().st_size > 0
        subtitle_details = str(subtitles)
    checks.append({"check": "subtitle_status", "ok": subtitle_ok, "details": subtitle_details})

    required_meta = ["title", "description", "tags"]
    missing = [k for k in required_meta if not metadata.get(k)]
    checks.append({"check": "metadata_completeness", "ok": len(missing) == 0, "details": {"missing": missing}})

    thumb_ok = bool(thumbnail and thumbnail.exists() and thumbnail.stat().st_size > 0)
    checks.append({"check": "thumbnail_presence", "ok": thumb_ok, "details": str(thumbnail) if thumbnail else None})

    all_ok = all(c["ok"] for c in checks)
    return {"ok": all_ok, "checks": checks, "duration_seconds": duration, "resolution": f"{width}x{height}"}


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Phase-4 quality control checks")
    parser.add_argument("--video", required=True)
    parser.add_argument("--metadata-json", required=True, help="Path to metadata json")
    parser.add_argument("--thumbnail")
    parser.add_argument("--subtitles")
    args = parser.parse_args()

    metadata = json.loads(Path(args.metadata_json).read_text(encoding="utf-8"))
    payload = run_quality_checks(
        video_path=args.video,
        metadata=metadata,
        thumbnail_path=args.thumbnail,
        subtitles_path=args.subtitles,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(_cli())

