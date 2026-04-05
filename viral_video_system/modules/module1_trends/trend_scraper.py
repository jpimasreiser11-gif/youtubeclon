import json
from datetime import datetime


def get_youtube_trending(niche, limit=20):
    try:
        import yt_dlp
    except Exception:
        return [
            {"title": f"{niche}: error comun que te cuesta dinero", "url": "mock://yt/1", "views": 100000},
            {"title": f"{niche}: 3 pasos para mejorar hoy", "url": "mock://yt/2", "views": 75000},
        ][:limit]

    ydl_opts = {"quiet": True, "extract_flat": True, "playlistend": limit}
    search_url = f"ytsearch{limit}:{niche} shorts {datetime.now().strftime('%Y')}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(search_url, download=False)
        entries = result.get("entries", []) if result else []
        out = []
        for e in entries:
            out.append({
                "title": e.get("title", ""),
                "url": e.get("url") or e.get("webpage_url") or "",
                "views": e.get("view_count", 0),
            })
        return out


def get_twitter_trends(niche, limit=15):
    try:
        import feedparser
    except Exception:
        return [f"{niche} tendencia {i}" for i in range(1, min(5, limit) + 1)]

    instances = ["https://nitter.poast.org", "https://nitter.privacydev.net"]
    for base in instances:
        try:
            feed_url = f"{base}/search/rss?q={niche}&f=tweets"
            feed = feedparser.parse(feed_url)
            titles = [entry.title for entry in feed.entries[:limit]]
            if titles:
                return titles
        except Exception:
            continue
    return []


def get_google_trends(niche):
    try:
        from pytrends.request import TrendReq
    except Exception:
        return [f"{niche} 2026", f"{niche} errores", f"{niche} tips"]

    pytrends = TrendReq(hl="es-ES", tz=60)
    pytrends.build_payload([niche], cat=0, timeframe="now 1-d")
    related = pytrends.related_queries()
    rising = (related.get(niche) or {}).get("rising")
    return rising["query"].tolist()[:10] if rising is not None else []


def scrape_all(niche):
    return {
        "youtube": get_youtube_trending(niche),
        "twitter": get_twitter_trends(niche),
        "google": get_google_trends(niche),
        "generated_at": datetime.utcnow().isoformat() + "Z",
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", default="finanzas personales")
    args = parser.parse_args()
    print(json.dumps(scrape_all(args.niche), ensure_ascii=False, indent=2))
