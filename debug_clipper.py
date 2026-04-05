import sys
import os
# Add scripts dir to path to import clipper
sys.path.append(os.path.join(os.getcwd(), 'scripts'))
import clipper

print("Debugging clipper...")
video_id = "jNQXAC9IVRw"
# Use a short clip test
clipper.process_clip(video_id, "test_clip", 0.0, 5.0, 0)
print("Clipping finished.")
