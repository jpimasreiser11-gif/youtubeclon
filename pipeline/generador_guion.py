from __future__ import annotations

import argparse
import json
import time
from typing import Any

from backend.database import get_channel, init_db
from backend.pipeline.script_writer import generate_script


def generate_script_json(
    topic: str,
    channel_id: str,
    retries: int = 3,
    retry_delay_seconds: float = 1.5,
    script_provider: str | None = None,
) -> dict[str, Any]:
    """Generate channel-aware script JSON with explicit retry/failure handling."""
    if not topic.strip():
        raise ValueError("topic is required")
    if not channel_id.strip():
        raise ValueError("channel_id is required")
    if retries < 1:
        raise ValueError("retries must be >= 1")

    init_db()
    channel = get_channel(channel_id)
    if not channel:
        raise ValueError(f"Channel not found: {channel_id}")

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            if script_provider:
                import os

                os.environ["SCRIPT_PROVIDER"] = script_provider
            result = generate_script(topic=topic, channel=channel)
            script_text = (result.get("script") or "").strip()
            title = (result.get("title") or "").strip()
            if not script_text or not title:
                raise RuntimeError("Script generator returned an invalid payload")
            return {
                "ok": True,
                "attempt": attempt,
                "channel_id": channel_id,
                "topic": topic,
                "script": {
                    "title": title,
                    "body": script_text,
                    "short_script": result.get("short_script", ""),
                    "seo_description": result.get("seo_description", ""),
                    "tags": result.get("tags", ""),
                    "broll_markers": result.get("broll_markers", []),
                    "word_count": int(result.get("word_count") or 0),
                    "script_path": result.get("script_path", ""),
                },
            }
        except Exception as exc:  # explicit fail + retry
            last_error = exc
            if attempt < retries:
                time.sleep(max(0.0, retry_delay_seconds * attempt))
                continue
            raise RuntimeError(
                f"Script generation failed after {retries} attempts for channel '{channel_id}': {exc}"
            ) from exc

    raise RuntimeError(f"Script generation failed: {last_error}")


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Phase-4 script generator wrapper")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--channel", required=True, dest="channel_id")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument(
        "--script-provider",
        choices=["auto", "local", "gemini"],
        default="local",
        help="Use local by default for free-first dry-runs",
    )
    args = parser.parse_args()
    payload = generate_script_json(
        topic=args.topic,
        channel_id=args.channel_id,
        retries=args.retries,
        script_provider=args.script_provider,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

