import os
import sys
import json
import time
from dotenv import load_dotenv

# Path management
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from src.utils.db_manager import get_video_by_id, update_video_status
from src.media_engine.tts_engine import generate_audio
from src.generators.asset_gatherer import get_pexels_images, download_asset
from src.media_engine.video_composer import VideoComposer

load_dotenv()

def produce_video(video_id):
    print(f"--- Starting Production for Video ID {video_id} ---")
    
    # 1. Load Data
    video = get_video_by_id(video_id)
    if not video or not video.script_content:
        print("Error: Video not found or missing script")
        return
        
    script = json.loads(video.script_content)
    niche = video.niche.capitalize()
    channel_dir = os.path.join(project_root, f"Channel-{niche}")
    assets_dir = os.path.join(channel_dir, "assets")
    
    # 2. Extract Keywords and Gather B-Roll
    print("Gathering Visual Assets...")
    keywords = script.get("visual_keywords", ["cinematic", "mystery"])
    image_paths = []
    
    for kw in keywords[:3]: # Limit for test
        print(f"Searching for: {kw}")
        results = get_pexels_images(kw, per_page=1)
        if results:
            path = download_asset(results[0]["link"], os.path.join(assets_dir, "B-Roll"), f"{kw.replace(' ', '_')}.jpg")
            if path: image_paths.append(path)
            
    if not image_paths:
        print("Error: No visual assets found")
        return

    # 3. Generate Audio
    print("Generating Dramatic Audio...")
    import asyncio
    voice_file = os.path.join(assets_dir, "Audio", f"voice_{video_id}.mp3")
    # Determine voice profile based on niche
    niche_key = video.niche.lower()
    
    # Combine hook and body for the full audio
    full_text = f"{script['hook']}\n\n{script['body']}"
    # Process tts asynchroneously
    audio_path = asyncio.run(generate_audio(full_text[:2000], voice_file, niche=niche_key))
    
    if not audio_path:
        print("Error: Audio generation failed")
        return
    
    # 4. Render Video
    print("Rendering Final Scene...")
    composer = VideoComposer(output_dir=os.path.join(channel_dir, "renders"))
    
    try:
        final_video = composer.render_scene_with_effects(
            voice_path=audio_path,
            image_paths=image_paths,
            scene_id=str(video_id)
        )
        print(f"VIDEO FINISHED: {final_video}")
        update_video_status(video_id, 'rendered')
    except Exception as e:
        print(f"Rendering Failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python video_producer.py <video_id>")
    else:
        produce_video(int(sys.argv[1]))
