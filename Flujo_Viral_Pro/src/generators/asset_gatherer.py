import os
import requests
import json
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()

def get_pexels_videos(query, per_page=5):
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("Error: PEXELS_API_KEY not found")
        return []

    headers = {"Authorization": api_key}
    url = f"https://api.pexels.com/videos/search?query={query}&per_page={per_page}&orientation=landscape"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        videos = []
        for v in data.get("videos", []):
            # Get the best quality link (usually HD)
            video_files = v.get("video_files", [])
            if video_files:
                # Find a reasonable resolution (e.g., width 1280 or 1920)
                best_file = None
                for f in video_files:
                    if f.get("width") == 1920:
                        best_file = f
                        break
                    if not best_file or (f.get("width") and f.get("width") > (best_file.get("width") or 0)):
                        best_file = f
                
                if best_file:
                    videos.append({
                        "id": v.get("id"),
                        "link": best_file.get("link"),
                        "duration": v.get("duration")
                    })
        return videos
    except Exception as e:
        print(f"Error searching Pexels for '{query}': {e}")
        return []

def download_asset(url, folder, filename):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    
    if os.path.exists(path):
        print(f"Asset already exists: {path}")
        return path
        
    try:
        print(f"Downloading asset from {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded: {path}")
        return path
    except Exception as e:
        print(f"Error downloading asset {url}: {e}")
        return None

def get_pexels_images(query, per_page=5):
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("Error: PEXELS_API_KEY not found")
        return []

    headers = {"Authorization": api_key}
    url = f"https://api.pexels.com/v1/search?query={query}&per_page={per_page}&orientation=landscape"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        images = []
        for p in data.get("photos", []):
            images.append({
                "id": p.get("id"),
                "link": p.get("src", {}).get("large2x") or p.get("src", {}).get("original"),
                "alt": p.get("alt")
            })
        return images
    except Exception as e:
        print(f"Error searching Pexels for images '{query}': {e}")
        return []
        
# ... (download_asset remains the same)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("folder", default="assets/temp")
    parser.add_argument("--type", choices=["video", "image"], default="video")
    args = parser.parse_args()
    
    if args.type == "video":
        results = get_pexels_videos(args.query, per_page=1)
    else:
        results = get_pexels_images(args.query, per_page=1)
        
    if results:
        ext = "mp4" if args.type == "video" else "jpg"
        download_asset(results[0]["link"], args.folder, f"{args.query.replace(' ', '_')}.{ext}")
    else:
        print(f"No {args.type}s found for query: {args.query}")
