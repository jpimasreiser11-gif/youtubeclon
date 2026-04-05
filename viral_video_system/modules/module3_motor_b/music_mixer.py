import os


def get_royalty_free_music(mood="motivational", duration_needed=60, dry_run=True):
    if dry_run:
        return None

    try:
        import requests
    except Exception:
        return None

    api_key = os.getenv("PIXABAY_API_KEY")
    if not api_key:
        return None

    url = "https://pixabay.com/api/videos/music/"
    params = {
        "key": api_key,
        "mood": mood,
        "duration_from": max(30, duration_needed - 30),
        "duration_to": duration_needed + 60,
        "per_page": 10,
    }

    try:
        r = requests.get(url, params=params, timeout=30)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        if not hits:
            return None
        track = hits[0]
        audio_url = track.get("audio")
        if not audio_url:
            return None
        data = requests.get(audio_url, timeout=30).content
        out = os.path.join("viral_video_system", "temp", "background_music.mp3")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as f:
            f.write(data)
        return out
    except Exception:
        return None
