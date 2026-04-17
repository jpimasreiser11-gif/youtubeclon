from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone

import requests

from backend.database import get_all_channels, get_channel, init_db, save_trend
from backend.pipeline.trend_finder import NICHE_KEYWORDS, NICHE_SUBREDDITS

USER_AGENT = {"User-Agent": "youtube-automation-pro/1.0"}


def _google_trends_topics(keywords: list[str], language: str) -> list[dict]:
    results: list[dict] = []
    try:
        from pytrends.request import TrendReq
    except Exception:
        return results
    try:
        pytrends = TrendReq(hl=language, tz=0, timeout=(8, 20))
        for kw in keywords[:3]:
            try:
                pytrends.build_payload([kw], timeframe="now 7-d")
                related = pytrends.related_queries()
                rising = related.get(kw, {}).get("rising") if isinstance(related, dict) else None
                if rising is None:
                    continue
                for _, row in rising.head(8).iterrows():
                    results.append(
                        {
                            "topic": str(row.get("query", "")).strip(),
                            "source": "google_trends",
                            "growth_rate": float(row.get("value", 0) or 0),
                        }
                    )
            except Exception:
                continue
    except Exception:
        return []
    return results


def _reddit_topics(subreddits: list[str]) -> list[dict]:
    results: list[dict] = []
    for sub in subreddits[:4]:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit=12"
            resp = requests.get(url, headers=USER_AGENT, timeout=12)
            if resp.status_code != 200:
                continue
            data = resp.json()
            posts = data.get("data", {}).get("children", [])
            for p in posts:
                d = p.get("data", {})
                score = int(d.get("score", 0))
                if score < 100:
                    continue
                results.append(
                    {
                        "topic": d.get("title", ""),
                        "source": "reddit",
                        "engagement": score,
                        "comments": int(d.get("num_comments", 0)),
                        "source_url": f"https://reddit.com{d.get('permalink', '')}",
                    }
                )
        except Exception:
            continue
    return results


def _news_topics(keywords: list[str], language: str) -> list[dict]:
    results: list[dict] = []
    lang = "es" if language.startswith("es") else "en"
    for kw in keywords[:3]:
        try:
            url = f"https://news.google.com/rss/search?q={kw.replace(' ', '+')}&hl={lang}"
            resp = requests.get(url, headers=USER_AGENT, timeout=12)
            if resp.status_code != 200:
                continue
            titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", resp.text)
            if not titles:
                titles = re.findall(r"<title>(.*?)</title>", resp.text)
            for t in titles[:8]:
                title = t.strip()
                if not title or title.lower() == "google news":
                    continue
                results.append({"topic": title, "source": "google_news"})
        except Exception:
            continue
    return results


def _score(topic: dict, keywords: list[str], niche_text: str) -> float:
    score = 20.0
    source = topic.get("source", "")
    if source == "google_trends":
        score += 30
    elif source == "reddit":
        score += 22
    elif source == "google_news":
        score += 18
    score += min(float(topic.get("growth_rate", 0)) / 30.0, 20.0)
    score += min(float(topic.get("engagement", 0)) / 200.0, 15.0)
    text = (topic.get("topic") or "").lower()
    keyword_hits = sum(1 for kw in keywords if kw.lower().split()[0] in text)
    score += min(keyword_hits * 4.0, 12.0)
    niche_hits = sum(1 for w in niche_text.lower().replace(",", " ").split() if len(w) > 4 and w in text)
    score += min(niche_hits * 1.5, 10.0)
    return round(min(score, 100.0), 2)


def detect_channel(channel_slug: str, limit: int = 10, save: bool = False) -> dict:
    init_db()
    channel = get_channel(channel_slug)
    if not channel:
        raise ValueError(f"Unknown channel: {channel_slug}")

    keywords = NICHE_KEYWORDS.get(channel_slug, [channel.get("niche", "trending topic")])
    subreddits = NICHE_SUBREDDITS.get(channel_slug, [])
    language = channel.get("language", "en")

    raw = []
    raw.extend(_google_trends_topics(keywords, language))
    raw.extend(_reddit_topics(subreddits))
    raw.extend(_news_topics(keywords, language))

    deduped: dict[str, dict] = {}
    for item in raw:
        topic = (item.get("topic") or "").strip()
        if not topic:
            continue
        key = topic.lower()[:80]
        if key not in deduped:
            deduped[key] = item
        else:
            if item.get("source") == "google_trends":
                deduped[key] = item

    scored = []
    for item in deduped.values():
        topic = dict(item)
        topic["priority_score"] = _score(topic, keywords, channel.get("niche", ""))
        scored.append(topic)
    scored.sort(key=lambda x: x["priority_score"], reverse=True)
    top = scored[:limit]

    if save:
        for topic in top:
            save_trend(
                channel_db_id=channel["id"],
                topic=topic["topic"],
                score=float(topic["priority_score"]),
                source=topic.get("source", "marketing_trend_detector"),
                context=topic,
            )

    return {
        "channel_id": channel_slug,
        "channel_name": channel.get("name", channel_slug),
        "keywords_used": keywords[:6],
        "sources_used": ["google_trends", "reddit", "google_news"],
        "result_count": len(top),
        "prioritized_topics": top,
    }


def detect_all(limit: int = 10, save: bool = False) -> dict:
    init_db()
    results = []
    for channel in get_all_channels():
        try:
            results.append(detect_channel(channel["channel_id"], limit=limit, save=save))
        except Exception as exc:
            results.append({"channel_id": channel["channel_id"], "error": str(exc)})
    return {"ok": True, "generated_at": datetime.now(timezone.utc).isoformat(), "results": results}


def _cli() -> int:
    parser = argparse.ArgumentParser(
        description="Detect trend signals from free sources (Google Trends, Reddit, Google News)."
    )
    parser.add_argument("--channel", help="Channel slug (default: run all 6 channels)")
    parser.add_argument("--limit", type=int, default=10, help="Max prioritized topics per channel")
    parser.add_argument("--save", action="store_true", help="Persist top topics into trends table")
    args = parser.parse_args()
    try:
        payload = detect_channel(args.channel, limit=args.limit, save=args.save) if args.channel else detect_all(limit=args.limit, save=args.save)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"trend_detector failed: {exc}",
                    "hint": "Try: python -m marketing_automation.trend_detector --channel dark-science --limit 8 --save",
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

