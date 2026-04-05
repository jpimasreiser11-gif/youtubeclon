import whisper
import os
import json
from moviepy import TextClip, CompositeVideoClip

# Patch PATH for ffmpeg (needed by whisper)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
bin_dir = os.path.join(project_root, "bin")
os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")

def get_word_timestamps(audio_path, model_size="base"):
    """
    Uses Whisper to get word-level timestamps.
    Note: Standard Whisper doesn't always provide perfect word stamps without extra logic,
    but can be approximated or handled by segmenting.
    """
    print(f"Transcribing audio: {audio_path}")
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_path, verbose=False, word_timestamps=True)
    
    words_data = []
    for segment in result.get("segments", []):
        for word in segment.get("words", []):
            words_data.append({
                "word": word["word"].strip(),
                "start": word["start"],
                "end": word["end"]
            })
    return words_data

def create_dynamic_subtitles(words_data, size=(1280, 720), font_size=60, color='yellow', stroke_color='black'):
    """
    Creates a list of TextClips for dynamic subtitles.
    Uses MoviePy v2.x syntax.
    """
    clips = []
    w, h = size
    
    for item in words_data:
        # Create clip for each word
        # In MoviePy v2, TextClip constructor parameters might differ slightly
        # For simplicity and compatibility, we use a basic TextClip
        txt = TextClip(
            text=item["word"].upper(),
            font_size=font_size,
            color=color,
            stroke_color=stroke_color,
            stroke_width=2,
            method='label' 
        ).with_duration(item["end"] - item["start"]).with_start(item["start"]).with_position(('center', h * 0.8))
        
        clips.append(txt)
    return clips

if __name__ == "__main__":
    # Test block
    print("Subtitle module ready.")
