"""
YouTube Automation Pro — Trend Finder
Detects trending topics from multiple sources and scores them for virality.
Sources: Google Trends, YouTube Data API, Reddit, Google News.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests

from ..config import env
from ..database import save_trend, log_api_usage, log_pipeline_step
from .runtime import QuotaManager

logger = logging.getLogger("trend-finder")
QUOTA = QuotaManager()

# ── Subreddit mappings per channel niche ──────────────────────
NICHE_SUBREDDITS = {
    "impacto-mundial": ["conspiracy", "UnresolvedMysteries", "history", "Glitch_in_the_Matrix"],
    "mentes-rotas": ["TrueCrime", "UnresolvedMysteries", "serialkillers", "TrueCrimeDiscussion"],
    "el-loco-de-la-ia": ["ChatGPT", "artificial", "MachineLearning", "Entrepreneur"],
    "mind-warp": ["psychology", "BehavioralEconomics", "neuroscience", "Manipulation"],
    "wealth-files": ["wallstreetbets", "fatFIRE", "Entrepreneur", "business"],
    "dark-science": ["space", "science", "Physics", "DeepSeaCreatures"],
}

NICHE_KEYWORDS = {
    "impacto-mundial": ["misterios sin resolver", "conspiraciones reales", "lugares prohibidos", "fenomenos inexplicables"],
    "mentes-rotas": ["casos sin resolver", "asesinos en serie", "psicologia criminal", "crimenes reales"],
    "el-loco-de-la-ia": ["herramientas IA gratis", "automatización IA", "ganar dinero IA", "inteligencia artificial"],
    "mind-warp": ["dark psychology", "cognitive bias", "human behavior", "psychological manipulation"],
    "wealth-files": ["billionaire secrets", "wealth building", "financial freedom", "entrepreneur mindset"],
    "dark-science": ["space discovery", "deep ocean mystery", "quantum physics", "scientific breakthrough"],
}


# ═══════════════════════════════════════════════════════════════
# Source 1: Google Trends (pytrends — free, no API key)
# ═══════════════════════════════════════════════════════════════

def _google_trends(keywords: list[str], language: str) -> list[dict]:
    """Get trending topics from Google Trends."""
    results = []
    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl=language, tz=0, timeout=(10, 30))

        for kw in keywords[:3]:  # Limit to avoid rate limiting
            try:
                pytrends.build_payload([kw], cat=0, timeframe="now 7-d")
                related = pytrends.related_queries()
                if kw in related and related[kw]["rising"] is not None:
                    for _, row in related[kw]["rising"].head(5).iterrows():
                        results.append({
                            "topic": row["query"],
                            "source": "google_trends",
                            "growth_rate": float(row.get("value", 0)),
                            "keyword": kw,
                        })
                time.sleep(2)  # Rate limit
            except Exception as exc:
                logger.warning(f"Google Trends error for '{kw}': {exc}")
                continue

        log_api_usage("google_trends", "related_queries", requests=len(keywords))
    except ImportError:
        logger.warning("pytrends not installed. Skipping Google Trends.")
    except Exception as exc:
        logger.error(f"Google Trends global error: {exc}")

    return results


# ═══════════════════════════════════════════════════════════════
# Source 2: YouTube Data API v3 (10,000 units/day free)
# ═══════════════════════════════════════════════════════════════

def _youtube_trending(keywords: list[str], language: str) -> list[dict]:
    """Find viral videos in the niche from YouTube."""
    api_key = env("YOUTUBE_DATA_API_KEY")
    if not api_key:
        logger.warning("No YouTube Data API key. Skipping YouTube trends.")
        return []

    results = []
    base_url = "https://www.googleapis.com/youtube/v3/search"

    for kw in keywords[:2]:
        if not QUOTA.allow("youtube_data_api", cost=1):
            logger.warning("YouTube Data API quota reached. Skipping remaining keyword calls.")
            break
        try:
            params = {
                "part": "snippet",
                "q": kw,
                "type": "video",
                "order": "viewCount",
                "publishedAfter": _days_ago_iso(3),
                "maxResults": 10,
                "key": api_key,
                "relevanceLanguage": language[:2],
            }
            resp = requests.get(base_url, params=params, timeout=15)
            if resp.status_code == 200:
                items = resp.json().get("items", [])
                for item in items:
                    snippet = item.get("snippet", {})
                    results.append({
                        "topic": snippet.get("title", ""),
                        "source": "youtube_api",
                        "source_url": f"https://youtube.com/watch?v={item['id'].get('videoId', '')}",
                        "channel": snippet.get("channelTitle", ""),
                        "published": snippet.get("publishedAt", ""),
                    })
                log_api_usage("youtube_data_api", "search", requests=1)
            time.sleep(1)
        except Exception as exc:
            logger.warning(f"YouTube API error for '{kw}': {exc}")

    return results


# ═══════════════════════════════════════════════════════════════
# Source 3: Reddit (PRAW — free, 60 req/min)
# ═══════════════════════════════════════════════════════════════

def _reddit_trending(subreddits: list[str]) -> list[dict]:
    """Find viral posts from relevant subreddits."""
    client_id = env("REDDIT_CLIENT_ID")
    client_secret = env("REDDIT_CLIENT_SECRET")
    user_agent = env("REDDIT_USER_AGENT", "youtube-automation-pro/1.0")

    if not client_id or not client_secret:
        # Fallback: scrape Reddit without auth (limited)
        return _reddit_scrape_fallback(subreddits)

    results = []
    try:
        import praw
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )

        for sub_name in subreddits[:4]:
            try:
                sub = reddit.subreddit(sub_name)
                for post in sub.hot(limit=10):
                    if post.score > 500:  # Only viral posts
                        results.append({
                            "topic": post.title,
                            "source": "reddit",
                            "source_url": f"https://reddit.com{post.permalink}",
                            "engagement": post.score,
                            "comments": post.num_comments,
                            "subreddit": sub_name,
                        })
                time.sleep(1)
            except Exception as exc:
                logger.warning(f"Reddit error for r/{sub_name}: {exc}")

        log_api_usage("reddit", "subreddit.hot", requests=len(subreddits))
    except ImportError:
        logger.warning("praw not installed. Using scrape fallback.")
        return _reddit_scrape_fallback(subreddits)

    return results


def _reddit_scrape_fallback(subreddits: list[str]) -> list[dict]:
    """Scrape Reddit without PRAW (no auth needed)."""
    results = []
    headers = {"User-Agent": "youtube-automation-pro/1.0"}

    for sub_name in subreddits[:3]:
        if not QUOTA.allow("reddit", cost=1):
            logger.warning("Reddit quota reached. Stopping scrape fallback.")
            break
        try:
            url = f"https://www.reddit.com/r/{sub_name}/hot.json?limit=10"
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for child in data.get("data", {}).get("children", []):
                    post = child.get("data", {})
                    if post.get("score", 0) > 200:
                        results.append({
                            "topic": post.get("title", ""),
                            "source": "reddit_scrape",
                            "source_url": f"https://reddit.com{post.get('permalink', '')}",
                            "engagement": post.get("score", 0),
                            "comments": post.get("num_comments", 0),
                            "subreddit": sub_name,
                        })
            time.sleep(2)
        except Exception as exc:
            logger.warning(f"Reddit scrape error for r/{sub_name}: {exc}")

    return results


# ═══════════════════════════════════════════════════════════════
# Source 4: Google News (scraping — free, no API)
# ═══════════════════════════════════════════════════════════════

def _google_news(keywords: list[str], language: str) -> list[dict]:
    """Scrape Google News for recent headlines."""
    results = []

    for kw in keywords[:2]:
        if not QUOTA.allow("google_trends", cost=1):
            logger.warning("News/trends quota reached. Skipping Google News calls.")
            break
        try:
            lang_param = "es" if language.startswith("es") else "en"
            url = f"https://news.google.com/rss/search?q={kw.replace(' ', '+')}&hl={lang_param}"
            resp = requests.get(url, timeout=15)
            if resp.status_code == 200:
                # Simple XML parsing for RSS
                titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", resp.text)
                if not titles:
                    titles = re.findall(r"<title>(.*?)</title>", resp.text)
                for title in titles[:5]:
                    if title and len(title) > 15 and title not in ("Google News",):
                        results.append({
                            "topic": title,
                            "source": "google_news",
                            "keyword": kw,
                        })
            time.sleep(1)
        except Exception as exc:
            logger.warning(f"Google News error for '{kw}': {exc}")

    return results


# ═══════════════════════════════════════════════════════════════
# Virality Scoring
# ═══════════════════════════════════════════════════════════════

def _score_topic(raw: dict, channel: dict) -> float:
    """
    Score a topic from 0-100 for virality potential.
    Weights: search volume 30%, growth 25%, engagement 20%,
             low competition 15%, niche relevance 10%.
    """
    score = 0.0

    # Search volume / engagement (30%)
    engagement = raw.get("engagement", 0)
    if engagement > 10000:
        score += 30
    elif engagement > 5000:
        score += 25
    elif engagement > 1000:
        score += 20
    elif engagement > 500:
        score += 15
    elif engagement > 100:
        score += 10
    else:
        score += 5

    # Growth rate (25%)
    growth = raw.get("growth_rate", 0)
    if growth > 1000:
        score += 25
    elif growth > 500:
        score += 20
    elif growth > 100:
        score += 15
    else:
        score += 8

    # Source engagement (20%)
    comments = raw.get("comments", 0)
    if comments > 500:
        score += 20
    elif comments > 100:
        score += 15
    elif comments > 50:
        score += 10
    else:
        score += 5

    # Low competition bonus (15%)
    source = raw.get("source", "")
    if source in ("google_trends", "google_news"):
        score += 12  # Trending but potentially low video competition
    elif source == "reddit":
        score += 10
    else:
        score += 5

    # Niche relevance (10%) — check if topic contains niche keywords
    topic_lower = raw.get("topic", "").lower()
    niche_lower = channel.get("niche", "").lower()
    niche_words = set(niche_lower.replace(",", "").split())
    matches = sum(1 for w in niche_words if w in topic_lower)
    if matches > 2:
        score += 10
    elif matches > 0:
        score += 6
    else:
        score += 3

    return min(100.0, score)


# ═══════════════════════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════════════════════

def find_trending_topics(channel: dict) -> list[dict]:
    """
    Find and score trending topics for a channel.
    Combines multiple sources, deduplicates, scores, and saves top 5.
    """
    channel_id = channel["channel_id"]
    language = channel.get("language", "es")
    keywords = NICHE_KEYWORDS.get(channel_id, [channel.get("niche", "trending")])
    subreddits = NICHE_SUBREDDITS.get(channel_id, [])

    logger.info(f"🔍 Finding trends for '{channel['name']}' ({channel_id})...")

    # Collect from all sources
    all_topics: list[dict] = []
    all_topics.extend(_google_trends(keywords, language))
    all_topics.extend(_youtube_trending(keywords, language))
    all_topics.extend(_reddit_trending(subreddits))
    all_topics.extend(_google_news(keywords, language))

    logger.info(f"   Raw topics found: {len(all_topics)}")

    # Deduplicate by similarity (simple approach)
    seen = set()
    unique: list[dict] = []
    for t in all_topics:
        key = t.get("topic", "").lower().strip()[:50]
        if key and key not in seen:
            seen.add(key)
            unique.append(t)

    # Score and sort
    scored = []
    for t in unique:
        t["score"] = _score_topic(t, channel)
        scored.append(t)
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Save top 5 to database
    top_5 = scored[:5]
    for t in top_5:
        save_trend(
            channel_db_id=channel["id"],
            topic=t["topic"],
            score=t["score"],
            source=t.get("source", ""),
            context=t,
        )

    log_pipeline_step(channel["id"], None, "trend_finder", "ok",
                      f"Found {len(top_5)} trending topics")
    logger.info(f"   ✅ Top {len(top_5)} trends saved for '{channel['name']}'")

    return top_5


def _days_ago_iso(days: int) -> str:
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
