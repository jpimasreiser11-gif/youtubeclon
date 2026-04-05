import os
import random
import requests
import json
from pathlib import Path

class BRollManager:
    def __init__(self, api_key: str, data_dir: str = None):
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/videos/search"
        
        # FASE 1 - QA Fix: Enforce correct storage path avoiding hardcoded or relative issues
        if data_dir is None or data_dir == "data":
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            data_dir = os.path.join(root_dir, "app", "storage")
            
        self.broll_dir = os.path.join(data_dir, "broll")
        self.fallback_dir = os.path.join(data_dir, "fallback_broll")
        
        os.makedirs(self.broll_dir, exist_ok=True)
        os.makedirs(self.fallback_dir, exist_ok=True)

    def _get_fallback_video(self) -> str | None:
        """Returns a random satisfying video from the fallback folder if available."""
        if not os.path.exists(self.fallback_dir):
            return None
            
        valid_exts = ['.mp4', '.mov']
        videos = [f for f in os.listdir(self.fallback_dir) if any(f.endswith(ext) for ext in valid_exts)]
        
        if not videos:
            return None
            
        selected = random.choice(videos)
        return os.path.join(self.fallback_dir, selected)

    def fetch_video(self, keyword: str, project_id: str, clip_index: int) -> str | None:
        """
        Queries Pexels for a portrait video matching the keyword.
        Returns the absolute path to the downloaded video, or a fallback if it fails.
        """
        print(f"🎬 B-Roll Manager: Searching for '{keyword}'...")
        
        if not self.api_key:
            print("⚠️ PEXELS_API_KEY no encontrada. Intentando fallback...")
            fallback = self._get_fallback_video()
            if fallback:
                print(f"✅ Usando video de fallback: {fallback}")
            return fallback

        headers = {"Authorization": self.api_key}
        params = {
            "query": keyword,
            "per_page": 1,
            "orientation": "portrait",
            "size": "small"
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            data = response.json()
            
            if data.get("videos"):
                video_files = data["videos"][0].get("video_files", [])
                
                # Fetch best vertical resolution (1080x1920 or similar mobile format)
                # First try to find one where width < height (portrait)
                vertical_files = [f for f in video_files if f.get("width", 0) < f.get("height", 0)]
                
                if vertical_files:
                    # Sort by resolution to get a good but not overly massive file
                    vertical_files.sort(key=lambda x: x.get("height", 0), reverse=True)
                    best_file = vertical_files[0]
                elif video_files:
                    best_file = video_files[0]
                else:
                    raise ValueError("No video files found inside Pexels response")
                    
                download_url = best_file["link"]
                
                # Download to project folder
                safe_kw = keyword.replace(" ", "_").replace("/", "").replace("\\", "")
                output_path = os.path.join(self.broll_dir, f"{project_id}_clip{clip_index}_{safe_kw}.mp4")
                
                print(f"⬇️ Pexels encontrado. Descargando B-Roll: {download_url[:50]}...")
                r = requests.get(download_url, stream=True, timeout=30)
                
                if r.status_code == 200:
                    with open(output_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"✅ B-Roll descargado: {output_path}")
                    return output_path
                else:
                    raise Exception(f"Error HTTP {r.status_code} al descargar de Pexels")
            else:
                print(f"⚠️ Pexels no encontró videos para '{keyword}'.")
                
        except Exception as e:
            print(f"❌ Pexels fetch failed: {str(e)}")
            
        # Fallback mechanism if Pexels fails or throws error
        fallback_path = self._get_fallback_video()
        if fallback_path:
            print(f"✅ Usando video B-Roll de fallback: {fallback_path}")
            return fallback_path
            
        print("❌ No hay videos Pexels ni fallback disponibles.")
        return None
