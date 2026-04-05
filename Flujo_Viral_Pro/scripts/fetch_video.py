import os
import requests
import argparse
import random
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

def fetch_video(keywords, output_path, orientation="portrait", size="medium"):
    if not PEXELS_API_KEY:
        print("Error: PEXELS_API_KEY not found in environment variables.")
        return

    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/videos/search?query={keywords}&orientation={orientation}&size={size}&per_page=5"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        if data["videos"]:
            video = random.choice(data["videos"])
            video_files = video["video_files"]
            target_res = "hd" if size == "medium" else "sd"
            best_video = next((v for v in video_files if v["quality"] == target_res), video_files[0])
            video_url = best_video["link"]
            
            print(f"Downloading video from {video_url}...")
            video_data = requests.get(video_url).content
            with open(output_path, "wb") as f:
                f.write(video_data)
            print(f"Saved to {output_path}")
        else:
            print("No videos found.")
    else:
        print(f"Error fetching from Pexels: {response.text}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    fetch_video(args.keywords, args.output)
