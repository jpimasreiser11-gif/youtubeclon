"""
Extract frames from output/jNQXAC9IVRw_clip_0.mp4
"""
from moviepy import VideoFileClip
from PIL import Image
import os

clip_path = "output/jNQXAC9IVRw_clip_0.mp4"

print("Extracting frames from new clip...")

clip = VideoFileClip(clip_path)

# Extract frames at different times
sample_times = [2.0, 5.0, 8.0, 11.0]

os.makedirs("output/frames", exist_ok=True)

for i, time in enumerate(sample_times):
    if time < clip.duration:
        frame = clip.get_frame(time)
        img = Image.fromarray(frame)
        output_path = f"output/frames/frame_{i+1}_at_{time:.1f}s.jpg"
        img.save(output_path, quality=95)
        print(f"Frame {i+1}: {time:.1f}s saved")

clip.close()

print("Done! Check output/frames/")
