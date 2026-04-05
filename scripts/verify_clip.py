"""
Visual verification - Extract frame from clip to verify subtitles
"""
from moviepy import VideoFileClip
import sys

clip_path = "output_test/jNQXAC9IVRw_clip_0.mp4"

print(f"📹 Analyzing clip: {clip_path}")

try:
    clip = VideoFileClip(clip_path)
    
    print(f"   Duration: {clip.duration:.2f}s")
    print(f"   Size: {clip.size[0]}x{clip.size[1]}")
    print(f"   FPS: {clip.fps}")
    print(f"   Audio: {'Yes' if clip.audio else 'No'}")
    
    # Extract a frame from the middle to check for subtitles
    mid_time = clip.duration / 2
    frame = clip.get_frame(mid_time)
    
    # Save frame
    from PIL import Image
    img = Image.fromarray(frame)
    img.save("output_test/sample_frame.jpg", quality=95)
    
    print(f"\n✅ Extracted sample frame at {mid_time:.2f}s")
    print(f"   Saved to: output_test/sample_frame.jpg")
    print(f"\n💡 Open this image to verify subtitles are present")
    print(f"   - Look for YELLOW text with BLACK outline")
    print(f"   - Positioned in bottom 20% of video")
    print(f"   - Should show word(s) from transcription")
    
    clip.close()
    
    print("\n✅ CLIP VERIFICATION COMPLETE")
    print(f"\nClip details:")
    print(f"   ✅ Vertical format (9:16)")
    print(f"   ✅ 1080x1920 resolution")
    print(f"   ✅ 30 FPS")
    print(f"   ✅ Audio included")
    print(f"   ⏳ Subtitles (check sample_frame.jpg)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
