"""
Quick pipeline test with short video for immediate verification
Uses jNQXAC9IVRw.mp4 (19 seconds) instead of the 34-minute video
"""
import os
import subprocess
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
import sys
from pathlib import Path

# Load environment variables
load_dotenv()

# Add ffmpeg to PATH
ffmpeg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
os.environ["PATH"] += os.pathsep + ffmpeg_dir

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Configuration - SHORT VIDEO
VIDEO_ID = "jNQXAC9IVRw"  # 19 seconds
DATA_DIR = "data"
OUTPUT_DIR = "output_test"  # Separate folder for test
CLIPPER_SCRIPT = r"scripts\clipper.py"

# Tools Paths
WHISPER_PATH = r"C:\Users\jpima\AppData\Roaming\Python\Python312\Scripts\whisper.exe"
FFMPEG_PATH = r"ffmpeg"

# Import functions from main pipeline
from full_pipeline import (
    extract_audio,
    transcribe_audio,
    extract_words_from_segments,
    detect_silences,
    run_clipper
)

def analyze_transcript_simple(transcript_data, silence_data):
    """Simplified analysis for short video - just create one clip"""
    print("Analyzing with Gemini (simplified for short video)...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    transcript_text = transcript_data['text']
    words = transcript_data.get('words', [])
    
    prompt = f"""
Analiza esta transcripción de un video muy corto ({len(transcript_text)} caracteres).

TRANSCRIPCIÓN: {transcript_text}

Crea 1 CLIP viral de este video corto:
- Debe usar TODO el contenido disponible
- Título atractivo
- Tiempo de inicio: 0.0
- Tiempo final: ajustado al contenido real (máximo 15 segundos)

Responde ÚNICAMENTE con JSON:
[{{"title": "Título descriptivo", "start_time": 0.0, "end_time": 15.0, "hook": "Descripción del gancho"}}]
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        json_match = re.search(r'\[.*\]', text, re.DOTALL)
        if json_match:
            clips = json.loads(json_match.group(0))
            print(f"✅ Gemini suggested {len(clips)} clip(s)")
            return clips
    except Exception as e:
        print(f"⚠️  Gemini failed, using fallback: {e}")
        return [{"title": "Video Completo", "start_time": 0.0, "end_time": 15.0, "hook": "Test"}]
    
    return []

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 QUICK PIPELINE TEST - SHORT VIDEO (19 seconds)")
    print("=" * 70)
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    print(f"\n📹 Using video: {VIDEO_ID} (~19 seconds)")
    input_video = f"{DATA_DIR}/{VIDEO_ID}.mp4"
    
    if not os.path.exists(input_video):
        print(f"❌ Video not found: {input_video}")
        sys.exit(1)
    
    # 1. Extract Audio
    print("\n[1/6] Extracting audio...")
    audio_path = extract_audio(input_video, VIDEO_ID)
    print(f"✅ Audio: {audio_path}")
    
    # 2. Transcribe
    print("\n[2/6] Transcribing (this takes ~30-60 seconds)...")
    transcript_data = transcribe_audio(VIDEO_ID, audio_path)
    print(f"✅ Transcript: {len(transcript_data['text'])} chars")
    print(f"   Words: {len(transcript_data.get('words', []))}")
    
    # 3. Detect Silences
    print("\n[3/6] Detecting silences...")
    silence_data = detect_silences(audio_path, VIDEO_ID)
    boundary_count = len(silence_data.get('boundary_points', []))
    print(f"✅ Found {boundary_count} silence boundaries")
    
    # 4. Analyze with Gemini (simplified)
    print("\n[4/6] Analyzing with Gemini...")
    clips = analyze_transcript_simple(transcript_data, silence_data)
    print(f"✅ Generated {len(clips)} clip suggestion(s)")
    
    # For short video, skip boundary adjustment (would be overkill)
    # Just clip the whole video
    
    # 5. Adjust output path for test
    print("\n[5/6] Generating clip with subtitles...")
    
    # Modify clipper call to use test output
    original_clipper = CLIPPER_SCRIPT
    
    # Create clip data
    clip_data = {
        'id': VIDEO_ID,
        'clips': clips,
        'words': transcript_data.get('words', [])
    }
    
    # Temporarily override output in clipper by modifying the data
    print(f"   Clip data prepared:")
    for i, clip in enumerate(clips):
        print(f"   - Clip {i}: {clip['title']}")
        print(f"     Time: {clip['start_time']:.1f}s - {clip['end_time']:.1f}s")
    
    # Run clipper
    print(f"\n[6/6] Running clipper...")
    
    # We need to modify output path - create a wrapper
    import tempfile
    import shutil
    
    # Run clipper
    subprocess.run([
        'python', CLIPPER_SCRIPT,
        json.dumps(clip_data)
    ], check=True)
    
    # Move files from output/ to output_test/
    for f in os.listdir('output'):
        if VIDEO_ID in f:
            src = os.path.join('output', f)
            dst = os.path.join(OUTPUT_DIR, f)
            shutil.move(src, dst)
            print(f"   ✅ Moved: {f} → {OUTPUT_DIR}/")
    
    print("\n" + "=" * 70)
    print("✅ QUICK TEST COMPLETE!")
    print("=" * 70)
    print(f"\n📁 Output location: {OUTPUT_DIR}/")
    print(f"   Check the generated clip(s) for:")
    print(f"   - Subtitles synchronized with speech")
    print(f"   - TikTok-style formatting (yellow text, black stroke)")
    print(f"   - 9:16 vertical aspect ratio")
    print("\n💡 This was a quick test. The main pipeline is still processing")
    print("   the longer video for comprehensive testing.")
