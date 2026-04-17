from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from backend.database import get_channel, init_db
from backend.pipeline.video_builder import build_video


def _concat_with_hooks(base_video: Path, intro: Path | None, outro: Path | None, output: Path) -> Path:
    clips = [p for p in [intro, base_video, outro] if p]
    if len(clips) == 1:
        return base_video
    list_file = output.with_suffix(".concat.txt")
    list_file.write_text("\n".join(f"file '{p.as_posix()}'" for p in clips), encoding="utf-8")
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-c:a",
        "aac",
        str(output),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    list_file.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(f"Failed to concat intro/outro hooks: {result.stderr[:400]}")
    return output


def assemble_video(
    channel_id: str,
    audio_path: str | Path,
    script_text: str,
    thumbnail_path: str | Path,
    clips: list[str | Path] | None = None,
    intro_hook_path: str | Path | None = None,
    outro_hook_path: str | Path | None = None,
) -> dict[str, Any]:
    """Build video via backend ffmpeg assembly (+subtitles/+remotion) and optional intro/outro hooks."""
    if not script_text.strip():
        raise ValueError("script_text is required")

    init_db()
    channel = get_channel(channel_id)
    if not channel:
        raise ValueError(f"Channel not found: {channel_id}")

    audio = Path(audio_path)
    thumbnail = Path(thumbnail_path)
    if not audio.exists():
        raise FileNotFoundError(f"Audio not found: {audio}")
    if not thumbnail.exists():
        raise FileNotFoundError(f"Thumbnail not found: {thumbnail}")

    clip_paths = [Path(c) for c in (clips or []) if Path(c).exists()]
    base_video = build_video(
        audio_path=audio,
        script_text=script_text,
        thumbnail_path=thumbnail,
        clips=clip_paths,
        channel=channel,
    )

    intro = Path(intro_hook_path) if intro_hook_path else None
    outro = Path(outro_hook_path) if outro_hook_path else None
    if intro and not intro.exists():
        raise FileNotFoundError(f"Intro hook not found: {intro}")
    if outro and not outro.exists():
        raise FileNotFoundError(f"Outro hook not found: {outro}")

    final_video = base_video
    if intro or outro:
        hooked = base_video.with_name(f"{base_video.stem}_hooked.mp4")
        final_video = _concat_with_hooks(base_video=base_video, intro=intro, outro=outro, output=hooked)

    return {
        "ok": True,
        "channel_id": channel_id,
        "video_path": str(final_video),
        "base_video_path": str(base_video),
        "hooks_applied": bool(intro or outro),
        "intro_hook": str(intro) if intro else None,
        "outro_hook": str(outro) if outro else None,
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Phase-4 pro video assembler wrapper")
    parser.add_argument("--channel", required=True, dest="channel_id")
    parser.add_argument("--audio", required=True)
    parser.add_argument("--script-file", required=True)
    parser.add_argument("--thumbnail", required=True)
    parser.add_argument("--clip", action="append", default=[])
    parser.add_argument("--intro-hook")
    parser.add_argument("--outro-hook")
    args = parser.parse_args()

    script_text = Path(args.script_file).read_text(encoding="utf-8")
    payload = assemble_video(
        channel_id=args.channel_id,
        audio_path=args.audio,
        script_text=script_text,
        thumbnail_path=args.thumbnail,
        clips=args.clip,
        intro_hook_path=args.intro_hook,
        outro_hook_path=args.outro_hook,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

