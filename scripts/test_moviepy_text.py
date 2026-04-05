"""
Simple test: Can MoviePy render text overlays?
"""
from moviepy import VideoFileClip, TextClip, CompositeVideoClip
import os

print("Testing MoviePy text overlay...")

# Load video
video_path = "data/jNQXAC9IVRw.mp4"
output_path = "output/simple_text_test.mp4"

print(f"Loading video: {video_path}")
video = VideoFileClip(video_path)

# Take first 5 seconds
clip = video.subclipped(0, 5)
w, h = clip.size

print(f"Video size: {w}x{h}")

# Create a simple text overlay
print("Creating text overlay...")
try:
    text = TextClip(
        text="TESTING",
        font='Arial-Bold',
        font_size=100,
        color='yellow',
        stroke_color='black',
        stroke_width=3,
        method='caption',
        size=(w, None)
    )
    
    # Position at center
    text = text.with_duration(5).with_position(('center', 'center'))
    
    print("Compositing...")
    final = CompositeVideoClip([clip, text])
    
    print("Rendering...")
    final.write_videofile(
        output_path,
        codec="libx264",
        audio_codec="aac",
        fps=30
    )
    
    print(f"\n✅ SUCCESS! Check {output_path}")
    print("If you see TESTING in yellow with black stroke, MoviePy text overlays work!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

finally:
    video.close()
