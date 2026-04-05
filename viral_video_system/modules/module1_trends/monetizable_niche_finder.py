from datetime import datetime

from viral_video_system.modules.module1_trends.trend_scraper import scrape_all


# Baseline CPM/revenue potential heuristics for English markets.
NICHE_SEEDS = [
    {"niche": "personal finance", "cpm": 9.8, "affiliate": 9.0, "sponsor": 9.0},
    {"niche": "investing for beginners", "cpm": 10.5, "affiliate": 9.5, "sponsor": 9.2},
    {"niche": "ai tools for business", "cpm": 8.9, "affiliate": 8.8, "sponsor": 9.1},
    {"niche": "software engineering career", "cpm": 7.8, "affiliate": 7.2, "sponsor": 8.4},
    {"niche": "productivity systems", "cpm": 6.8, "affiliate": 7.0, "sponsor": 7.3},
    {"niche": "side hustle ideas", "cpm": 7.4, "affiliate": 8.2, "sponsor": 7.5},
    {"niche": "ecommerce growth", "cpm": 8.1, "affiliate": 8.6, "sponsor": 8.3},
    {"niche": "credit cards and debt", "cpm": 10.2, "affiliate": 9.1, "sponsor": 8.7},
    {"niche": "tax optimization", "cpm": 11.1, "affiliate": 8.0, "sponsor": 8.8},
    {"niche": "saas marketing", "cpm": 8.6, "affiliate": 8.2, "sponsor": 9.0},
]


def _score_trend_signal(trends):
    yt = trends.get("youtube") or []
    google = trends.get("google") or []
    tw = trends.get("twitter") or []

    if not yt:
        return 25.0

    views = [int(item.get("views") or 0) for item in yt]
    avg_views = sum(views) / max(1, len(views))

    # Normalize avg views into 0..40 score.
    if avg_views <= 1000:
        yt_score = 8.0
    elif avg_views <= 10000:
        yt_score = 18.0
    elif avg_views <= 50000:
        yt_score = 28.0
    else:
        yt_score = 38.0

    google_score = min(25.0, len(google) * 3.0)
    tw_score = min(12.0, len(tw) * 1.5)

    return yt_score + google_score + tw_score


def _english_keywords_from_titles(titles, max_items=6):
    words = []
    skip = {
        "the", "and", "for", "with", "from", "this", "that", "your", "you", "are", "how", "what", "when",
        "why", "into", "about", "without", "shorts", "video", "videos", "best", "tips", "guide",
    }
    for title in titles:
        for token in str(title).lower().replace("-", " ").replace("/", " ").split():
            t = "".join(ch for ch in token if ch.isalpha())
            if len(t) < 5 or t in skip:
                continue
            words.append(t)
            if len(words) >= 40:
                break
    if not words:
        return ["money", "growth", "strategy", "business", "automation"]

    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1

    ranked = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in ranked[:max_items]]


def discover_top_monetizable_niches_en(limit=5):
    ranked = []

    for seed in NICHE_SEEDS:
        niche = seed["niche"]
        trends = scrape_all(niche)
        trend_score = _score_trend_signal(trends)

        monetization_score = (
            seed["cpm"] * 3.2
            + seed["affiliate"] * 2.5
            + seed["sponsor"] * 2.3
        )

        total = round(min(100.0, monetization_score + trend_score * 0.55), 2)

        yt_titles = [item.get("title", "") for item in (trends.get("youtube") or [])]
        keywords = _english_keywords_from_titles(yt_titles)

        ranked.append(
            {
                "niche": niche,
                "score": total,
                "monetization_score": round(monetization_score, 2),
                "trend_score": round(trend_score, 2),
                "suggested_keywords": keywords,
                "sample_titles": yt_titles[:3],
            }
        )

    ranked.sort(key=lambda x: x["score"], reverse=True)
    best = ranked[: max(1, int(limit))]

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "language": "en",
        "best_niches": best,
        "selected_niche": best[0]["niche"],
        "selection_reason": "Highest combined monetization + trend signal score",
    }
