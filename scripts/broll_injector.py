import os
import requests
import subprocess
import json
import argparse
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

class BRollInjector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/videos/search"

    def search_video(self, query):
        if not self.api_key:
            print("⚠️ PEXELS_API_KEY not found. Skipping B-roll.")
            return None
            
        headers = {"Authorization": self.api_key}
        params = {
            "query": query,
            "per_page": 1,
            "orientation": "portrait",
            "size": "small"
        }
        
        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            data = response.json()
            if data.get("videos"):
                # Get the best link (usually the first one)
                video = data["videos"][0]
                video_files = video.get("video_files", [])
                # Filter for mobile/portrait files
                best_file = next((f for f in video_files if f.get("width", 0) < f.get("height", 0)), video_files[0])
                return best_file["link"]
        except Exception as e:
            print(f"❌ Pexels search failed: {e}")
        return None

    def download_broll(self, url, output_path):
        print(f"⬇️ Downloading B-Roll: {url}")
        r = requests.get(url, stream=True)
        with open(output_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: f.write(chunk)
        return output_path

    def inject_broll(self, main_video, broll_video, output_path, start_time, duration=3.0):
        """Overlay B-roll on top of main video using FFmpeg"""
        # Complex filter: scale B-roll to match, then overlay at specific time
        # We also need to loop or trim the B-roll if it's too short/long
        filter_complex = (
            f"[1:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[broll];"
            f"[0:v][broll]overlay=0:0:enable='between(t,{start_time},{start_time+duration})'[outv]"
        )
        
        cmd = [
            'ffmpeg', '-y', '-i', main_video, '-i', broll_video,
            '-filter_complex', filter_complex,
            '-map', '[outv]', '-map', '0:a',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'copy',
            output_path
        ]
        
        print(f"🎬 Injecting B-Roll overlay at {start_time}s...")
        subprocess.run(cmd, check=True)
        return output_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--keywords", required=True) # JSON list
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    keywords = json.loads(args.keywords)
    injector = BRollInjector(PEXELS_API_KEY)
    
    current_video = args.video
    for i, kw in enumerate(keywords[:2]): # Limit to 2 B-rolls for now
        link = injector.search_video(kw)
        if link:
            temp_broll = f"temp_broll_{i}.mp4"
            injector.download_broll(link, temp_broll)
            
            # Simple logic: insert first B-roll at 5s, second at 15s (if long enough)
            start_t = 5.0 + (i * 10.0)
            result_video = f"injected_{i}.mp4"
            injector.inject_broll(current_video, temp_broll, result_video, start_t)
            current_video = result_video
            os.remove(temp_broll)
            
    os.rename(current_video, args.output)
    print(f"✅ B-Roll Injection Complete: {args.output}")
