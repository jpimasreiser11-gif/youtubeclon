import json
import argparse
import os
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.video.fx import Resize

def create_pop_subtitle(word_data, video_w, video_h, font="Arial-Bold", fontsize=70):
    """
    Creates a TextClip for a single word with a 'pop' (zoom) effect.
    """
    word = word_data["word"].upper()
    start = word_data["start"]
    end = word_data["end"]
    duration = end - start
    
    if duration <= 0:
        return None

    # Style: Yellow for high probability/emphasis, white otherwise
    color = "yellow" if word_data.get("probability", 1.0) > 0.9 else "white"
    
    # Create the base TextClip
    # Note: method='caption' or 'label'. 'label' is better for individual words.
    txt = TextClip(
        text=word,
        font=font,
        font_size=fontsize,
        color=color,
        stroke_color="black",
        stroke_width=2,
        method="label"
    ).with_start(start).with_duration(duration)

    # Position: Bottom center (around 80% height)
    txt = txt.with_position(('center', int(video_h * 0.8)))

    # Pop Effect: Resize from 0.8 to 1.0 in first 0.1s
    def zoom(t):
        if t < 0.1:
            return 0.8 + (t / 0.1) * 0.2
        return 1.0

    txt = txt.transform(lambda get_frame, t: vfx.Resize(zoom(t)).apply(get_frame(t)))
    # wait, moviepy v2 syntax for transform/resize is different.
    # Let's use simpler resize if transform is risky.
    # In MoviePy v2: clip.effects.resize(...)
    
    return txt

def render_video(video_path, transcript_path, output_path):
    clip = VideoFileClip(video_path)
    w, h = clip.size
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    words = data.get("words", [])
    
    subtitles = []
    # Optimization: Only process words within video duration
    for word_info in words:
        if word_info["start"] > clip.duration:
            break
        
        # Simple non-animated version first for stability
        txt = TextClip(
            text=word_info["word"].upper(),
            font_size=80,
            color="white",
            stroke_color="black",
            stroke_width=2,
            font="Arial-Bold",
            method="label"
        ).with_start(word_info["start"]).with_duration(word_info["end"] - word_info["start"]).with_position(('center', h*0.8))
        
        subtitles.append(txt)

    # Combine video with all subtitle clips
    final_video = CompositeVideoClip([clip] + subtitles)
    
    # Write final file
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=clip.fps, preset="ultrafast")
    
    return {"status": "success", "output": output_path}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sovereign Viral Renderer")
    parser.add_argument("--video", required=True)
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--output", required=True)
    
    args = parser.parse_args()
    
    # Ensure ImageMagick is configured (common issue on Windows)
    # os.environ["IMAGEMAGICK_BINARY"] = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
    
    result = render_video(args.video, args.transcript, args.output)
    print(json.dumps(result))
