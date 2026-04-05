"""
Extract multiple frames to verify subtitles at different timestamps
"""
from moviepy import VideoFileClip
from PIL import Image
import os

clip_path = "output_test/jNQXAC9IVRw_clip_0.mp4"

print(f"📹 Extracting multiple frames from: {clip_path}\n")

clip = VideoFileClip(clip_path)

# Extract frames at different times
sample_times = [2.0, 5.0, 8.0, 11.0]

os.makedirs("output_test/frames", exist_ok=True)

for i, time in enumerate(sample_times):
    if time < clip.duration:
        frame = clip.get_frame(time)
        img = Image.fromarray(frame)
        output_path = f"output_test/frames/frame_{i+1}_at_{time:.1f}s.jpg"
        img.save(output_path, quality=95)
        print(f"✅ Frame {i+1}: {time:.1f}s → {output_path}")

clip.close()

print(f"\n✅ Extracted {len(sample_times)} frames")
print(f"📁 Check output_test/frames/ folder")
print(f"\n💡 Look for YELLOW text with BLACK stroke in the bottom 20% of frames")
