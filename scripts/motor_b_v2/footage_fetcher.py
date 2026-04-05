import os
import random
import time
from typing import Optional, List, Dict

import requests


class FootageFetcher:
    def __init__(self):
        self.pexels_key = os.getenv("PEXELS_API_KEY", "").strip()
        self.pixabay_key = os.getenv("PIXABAY_API_KEY", "").strip()

        self.query_map = {
            "mystery": ["dark forest night", "abandoned building", "foggy night", "old archive", "night road"],
            "paranormal": ["mysterious lights", "storm sky", "empty field night", "old house"],
            "historical_enigma": ["ancient ruins", "old manuscript", "archaeology", "historic temple"],
        }

    def fetch_from_pexels(self, query: str, output_path: str, orientation: str = "portrait") -> Optional[str]:
        if not self.pexels_key:
            return None
        headers = {"Authorization": self.pexels_key}
        params = {"query": query, "orientation": orientation, "size": "large", "per_page": 10}

        r = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params, timeout=20)
        if r.status_code != 200:
            return None

        videos = (r.json() or {}).get("videos") or []
        if not videos:
            return None

        video = random.choice(videos[:5])
        files = video.get("video_files") or []
        portrait = [f for f in files if int(f.get("width", 0)) < int(f.get("height", 0))]
        chosen = portrait[0] if portrait else (files[0] if files else None)
        if not chosen or not chosen.get("link"):
            return None

        v = requests.get(chosen["link"], timeout=60, stream=True)
        if v.status_code != 200:
            return None
        with open(output_path, "wb") as f:
            for chunk in v.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        return output_path

    def fetch_from_pixabay(self, query: str, output_path: str) -> Optional[str]:
        if not self.pixabay_key:
            return None

        params = {"key": self.pixabay_key, "q": query, "video_type": "film", "per_page": 10, "safesearch": "true"}
        r = requests.get("https://pixabay.com/api/videos/", params=params, timeout=20)
        if r.status_code != 200:
            return None

        hits = (r.json() or {}).get("hits") or []
        if not hits:
            return None

        hit = random.choice(hits[:5])
        videos = hit.get("videos") or {}
        for quality in ("large", "medium", "small", "tiny"):
            item = videos.get(quality)
            if item and item.get("url"):
                v = requests.get(item["url"], timeout=60, stream=True)
                if v.status_code != 200:
                    return None
                with open(output_path, "wb") as f:
                    for chunk in v.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                return output_path
        return None

    def fetch_batch_for_script(self, visual_prompts: List[str], category: str, output_dir: str) -> List[Dict[str, str]]:
        os.makedirs(output_dir, exist_ok=True)
        clips = []
        fallback_queries = self.query_map.get(category, self.query_map["mystery"])

        for i, prompt in enumerate(visual_prompts):
            out = os.path.join(output_dir, f"footage_{i:02d}.mp4")
            query = (prompt.split(",")[0] or random.choice(fallback_queries)).strip()

            fetched = self.fetch_from_pexels(query, out)
            if fetched is None:
                time.sleep(0.25)
                fetched = self.fetch_from_pixabay(query, out)
            if fetched is None:
                fallback_query = random.choice(fallback_queries)
                fetched = self.fetch_from_pexels(fallback_query, out) or self.fetch_from_pixabay(fallback_query, out)

            if fetched:
                clips.append({"path": fetched, "type": "real", "scene": i})
            else:
                clips.append({"path": "", "type": "ai_needed", "scene": i, "prompt": prompt})

        return clips
