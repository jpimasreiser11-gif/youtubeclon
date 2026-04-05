import os
import json
import argparse
import random
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, ImageClip, ColorClip
import moviepy.video.fx.all as vfx
import subprocess

def run_tts(text, output_path):
    # Call existing tts.py
    subprocess.run(["python", "scripts/tts.py", "--text", text, "--output", output_path], check=True)

def run_fetch(keywords, output_path):
    # Call existing fetch_video.py
    # TODO: Add logic to fetch images if video fails or for variety
    subprocess.run(["python", "scripts/fetch_video.py", "--keywords", keywords, "--output", output_path], check=False)

def create_section_clip(section_data, index):
    audio_path = f"temp/section_{index}.mp3"
    video_path = f"temp/section_{index}.mp4"
    
    print(f"--- Processing Section {index}: {section_data['title']} ---")
    
    # 1. TTS
    if not os.path.exists(audio_path):
        run_tts(section_data['text'], audio_path)
    
    audio = AudioFileClip(audio_path)
    duration = audio.duration
    
    # 2. Visuals
    if not os.path.exists(video_path):
        run_fetch(section_data['visual_keywords'], video_path)
    
    if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
        video = VideoFileClip(video_path)
        # Loop if needed
        if video.duration < duration:
            video = vfx.loop(video, duration=duration)
        video = video.subclip(0, duration)
    else:
        # Fallback to black screen or placeholder if fetch fails
        print("Warning: No video found, using black screen.")
        # Create a black color clip 1080x1920 (Vertical) or 1920x1080 (Horizontal)
        # Defaulting to 1920x1080 for Long Form
        video = ColorClip(size=(1920, 1080), color=(0,0,0), duration=duration)
        
    video = video.set_audio(audio)
    
    # 3. Resize to Vertical (or Landscape? User said YouTube Long Form usually is 16:9, but this project started as Shorts)
    # User said "videos como en youtube de unos 15 minutois", usually 16:9.
    # Let's assume 16:9 for long form documentary.
    # But current fetch_video downloads portrait. We need to override.
    
    # For now keeping it compatible with existing fetcher (which does portrait).
    # TODO: Make fetcher support landscape.
    
    return video

def combine_sections(script_json_path, output_path):
    with open(script_json_path, "r", encoding='utf-8') as f:
        data = json.load(f)
        
    clips = []
    for i, section in enumerate(data['script_blocks']):
        clip = create_section_clip(section, i)
        clips.append(clip)
        
    final_video = concatenate_videoclips(clips)
    
    # Background Music (Optional)
    # music = AudioFileClip("assets/music.mp3").volumex(0.1).loop(duration=final_video.duration)
    # final_audio = CompositeAudioClip([final_video.audio, music])
    # final_video = final_video.set_audio(final_audio)
    
    final_video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    
    combine_sections(args.script, args.output)
