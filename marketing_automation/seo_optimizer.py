from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone

from backend.config import ROOT
from backend.database import get_all_channels, get_channel, get_videos, init_db

TITLE_MIN = 45
TITLE_MAX = 68


def _read_keywords(channel_slug: str) -> tuple[list[str], list[str]]:
    seo_file = ROOT / "marketing" / channel_slug / "seo_strategy.md"
    if not seo_file.exists():
        return [], []
    text = seo_file.read_text(encoding="utf-8")
    lines = [ln.strip().lstrip("-").strip() for ln in text.splitlines()]

    def _extract(after_heading: str, before_heading: str | None = None) -> list[str]:
        start = text.find(after_heading)
        if start < 0:
            return []
        section = text[start:]
        if before_heading:
            end = section.find(before_heading)
            if end > 0:
                section = section[:end]
        return [ln for ln in [x.strip().lstrip("-").strip() for x in section.splitlines()] if ln and not ln.startswith("#")]

    core = _extract("## Main YouTube keywords", "## Long-tail keywords")[:10]
    long_tail = _extract("## Long-tail keywords", "##")[:10]
    if not core:
        core = [ln for ln in lines if "keyword" not in ln.lower()][:8]
    return core, long_tail


def _parse_tags(raw: str | list | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    txt = str(raw).strip()
    if not txt:
        return []
    try:
        loaded = json.loads(txt)
        if isinstance(loaded, list):
            return [str(x).strip() for x in loaded if str(x).strip()]
    except Exception:
        pass
    return [x.strip() for x in re.split(r"[,\n;]", txt) if x.strip()]


def _suggest_for_video(video: dict, core_keywords: list[str], long_tail: list[str]) -> dict:
    title = (video.get("title") or "").strip()
    metadata = {}
    try:
        metadata = json.loads(video.get("metadata_json") or "{}")
    except Exception:
        metadata = {}
    description = str(metadata.get("description") or "")
    tags = _parse_tags(metadata.get("tags"))
    ctr = float(video.get("ctr") or 0)
    retention = float(video.get("retention") or 0)

    suggestions: list[str] = []
    if len(title) < TITLE_MIN:
        suggestions.append(f"Title is short ({len(title)} chars). Target {TITLE_MIN}-{TITLE_MAX} chars.")
    elif len(title) > TITLE_MAX:
        suggestions.append(f"Title is long ({len(title)} chars). Target {TITLE_MIN}-{TITLE_MAX} chars.")

    primary_kw = core_keywords[0] if core_keywords else ""
    if primary_kw and primary_kw.lower() not in title.lower():
        suggestions.append(f"Include primary keyword early in title: '{primary_kw}'.")
    if description and primary_kw and primary_kw.lower() not in description.lower():
        suggestions.append("First description lines should include the primary keyword.")
    if len(tags) < 5:
        suggestions.append("Use at least 5 tags (2 core + 3 long-tail).")

    if ctr < 3.0:
        suggestions.append("CTR is low (<3%). Test a stronger title contrast and value promise.")
    if retention and retention < 35:
        suggestions.append("Retention is low (<35%). Front-load payoff in first 30 seconds.")

    recommended_tags = []
    for kw in [*core_keywords[:3], *long_tail[:5]]:
        if kw and kw.lower() not in {t.lower() for t in tags}:
            recommended_tags.append(kw)
    recommended_title = title
    if primary_kw and primary_kw.lower() not in title.lower():
        recommended_title = f"{primary_kw.title()}: {title}"[:TITLE_MAX]

    return {
        "video_id": video.get("id"),
        "title": title,
        "metrics": {"ctr": ctr, "retention": retention, "views": int(video.get("views") or 0)},
        "suggestions": suggestions or ["Metadata looks healthy. Keep monitoring at 72h."],
        "recommended_title_variant": recommended_title,
        "recommended_tags_to_add": recommended_tags[:8],
    }


def analyze_channel(channel_slug: str, limit: int = 10) -> dict:
    init_db()
    channel = get_channel(channel_slug)
    if not channel:
        raise ValueError(f"Unknown channel: {channel_slug}")
    core_keywords, long_tail = _read_keywords(channel_slug)
    videos = get_videos(channel_id=channel["id"], limit=limit, offset=0)

    if not videos:
        baseline = {
            "channel_id": channel_slug,
            "channel_name": channel.get("name", channel_slug),
            "message": "No videos found in SQLite. Returning keyword-based baseline suggestions.",
            "core_keywords": core_keywords[:6],
            "long_tail_keywords": long_tail[:6],
            "suggestions": [
                "Use one core keyword at the start of every new title.",
                "Keep title length close to 55-65 characters.",
                "Description line 1: promise + keyword; line 2: proof/context.",
                "Use 5-8 tags (2 core, 3 long-tail, 1-3 timely).",
            ],
        }
        return {"ok": True, "generated_at": datetime.now(timezone.utc).isoformat(), "results": [baseline]}

    analyses = [_suggest_for_video(v, core_keywords, long_tail) for v in videos]
    avg_ctr = round(sum(float(v.get("ctr") or 0) for v in videos) / len(videos), 2)
    avg_retention = round(sum(float(v.get("retention") or 0) for v in videos) / len(videos), 2)
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results": [
            {
                "channel_id": channel_slug,
                "channel_name": channel.get("name", channel_slug),
                "video_count_analyzed": len(videos),
                "avg_ctr": avg_ctr,
                "avg_retention": avg_retention,
                "core_keywords": core_keywords[:6],
                "long_tail_keywords": long_tail[:6],
                "video_recommendations": analyses,
            }
        ],
    }


def analyze_all_channels(limit: int = 10) -> dict:
    init_db()
    channels = get_all_channels()
    results = []
    for channel in channels:
        try:
            res = analyze_channel(channel["channel_id"], limit=limit)["results"][0]
            results.append(res)
        except Exception as exc:
            results.append({"channel_id": channel["channel_id"], "ok": False, "error": str(exc)})
    return {"ok": True, "generated_at": datetime.now(timezone.utc).isoformat(), "results": results}


def _cli() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze metadata + performance proxies (CTR/retention) and propose SEO improvements."
    )
    parser.add_argument("--channel", help="Channel slug (default: all 6 channels)")
    parser.add_argument("--limit", type=int, default=10, help="Videos per channel to analyze")
    args = parser.parse_args()
    try:
        payload = analyze_channel(args.channel, limit=args.limit) if args.channel else analyze_all_channels(limit=args.limit)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"seo_optimizer failed: {exc}",
                    "hint": "Try: python -m marketing_automation.seo_optimizer --channel mind-warp --limit 8",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

