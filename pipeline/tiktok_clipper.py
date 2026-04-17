from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any


def _duration_seconds(path: Path) -> float:
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {path}: {result.stderr[:300]}")
    data = json.loads(result.stdout or "{}")
    return float((data.get("format") or {}).get("duration") or 0.0)


def _parse_srt_windows(srt_path: Path) -> list[tuple[float, float]]:
    if not srt_path.exists():
        return []
    raw = srt_path.read_text(encoding="utf-8", errors="ignore")
    matches = re.findall(r"(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})", raw)
    windows: list[tuple[float, float]] = []

    def to_sec(ts: str) -> float:
        h, m, rest = ts.split(":")
        s, ms = rest.split(",")
        return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

    for start, end in matches:
        s = to_sec(start)
        e = to_sec(end)
        if e > s:
            windows.append((s, e))
    return windows


def _choose_best_segment(duration: float, srt_path: Path | None, clip_seconds: int) -> tuple[float, float, str]:
    if srt_path:
        windows = _parse_srt_windows(srt_path)
        if windows:
            merged: list[tuple[float, float]] = []
            curr_start, curr_end = windows[0]
            for s, e in windows[1:]:
                if s - curr_end <= 1.2:
                    curr_end = e
                else:
                    merged.append((curr_start, curr_end))
                    curr_start, curr_end = s, e
            merged.append((curr_start, curr_end))

            best = max(merged, key=lambda seg: seg[1] - seg[0])
            center = (best[0] + best[1]) / 2
            start = max(0.0, min(center - clip_seconds / 2, max(0.0, duration - clip_seconds)))
            end = min(duration, start + clip_seconds)
            return start, end, "srt_heuristic"

    start = max(0.0, (duration / 2) - (clip_seconds / 2))
    end = min(duration, start + clip_seconds)
    return start, end, "center_fallback"


def create_tiktok_clip(
    video_path: str | Path,
    output_path: str | Path | None = None,
    subtitles_path: str | Path | None = None,
    clip_seconds: int = 45,
) -> dict[str, Any]:
    """Create 9:16 MP4 short using best segment heuristic."""
    video = Path(video_path)
    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video}")
    if clip_seconds < 10 or clip_seconds > 120:
        raise ValueError("clip_seconds must be between 10 and 120")

    out = Path(output_path) if output_path else video.with_name(f"{video.stem}_tiktok.mp4")
    duration = _duration_seconds(video)
    if duration <= 0:
        raise RuntimeError("Input video has invalid duration")

    srt = Path(subtitles_path) if subtitles_path else None
    start, end, strategy = _choose_best_segment(duration, srt, clip_seconds)
    segment_len = max(1.0, end - start)
    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{start:.3f}",
        "-i",
        str(video),
        "-t",
        f"{segment_len:.3f}",
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-c:a",
        "aac",
        "-b:a",
        "160k",
        "-movflags",
        "+faststart",
        str(out),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg tiktok clip failed: {result.stderr[:500]}")
    if not out.exists() or out.stat().st_size == 0:
        raise RuntimeError("TikTok clip was not created")

    return {
        "ok": True,
        "input_video": str(video),
        "output_video": str(out),
        "strategy": strategy,
        "segment_start": round(start, 3),
        "segment_end": round(end, 3),
        "target_aspect": "9:16",
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Phase-4 TikTok clipper")
    parser.add_argument("--video", required=True)
    parser.add_argument("--output")
    parser.add_argument("--subtitles")
    parser.add_argument("--clip-seconds", type=int, default=45)
    args = parser.parse_args()
    payload = create_tiktok_clip(
        video_path=args.video,
        output_path=args.output,
        subtitles_path=args.subtitles,
        clip_seconds=args.clip_seconds,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

