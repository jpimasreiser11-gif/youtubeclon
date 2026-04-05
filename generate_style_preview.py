import sys
import os
import numpy as np
from PIL import Image
from pathlib import Path

# Add scripts directory to path
sys.path.append(os.path.join(os.getcwd(), 'scripts'))
from pil_subtitle_renderer import render_subtitles_on_frame

def generate_preview():
    # Create a dark gray frame (representing a video frame)
    w, h = 1080, 1920
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    frame[:] = [40, 40, 40] # Dark gray background
    
    # Mock words
    words = [
        {"word": "CHOOSE", "start": 0.0, "end": 1.0},
        {"word": "A", "start": 0.0, "end": 1.0},
        {"word": "STYLE", "start": 0.0, "end": 2.0},
    ]
    
    # We want to show "CHOOSE A STYLE" but the fix will take the latest word
    # if they overlap. If the user wants multiple words, they should not overlap.
    # For preview, let's just show one word "STYLE" in Hormozi green
    
    # The fix I added:
    # if len(active_words) > 1:
    #     active_words = [sorted(active_words, key=lambda x: x['start'], reverse=True)[0]]
    
    # If we want to show the green highlight:
    rendered_frame = render_subtitles_on_frame(frame, words, 0.5, (w, h), style_name="HORMOZI")
    
    # Save preview
    output_dir = os.path.join(os.getcwd(), 'app', 'public', 'previews')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, 'subtitle_style_preview.png')
    img = Image.fromarray(rendered_frame)
    img.save(output_path)
    print(f"Preview saved to: {output_path}")

if __name__ == "__main__":
    generate_preview()
