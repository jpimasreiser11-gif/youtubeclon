from moviepy import VideoClip, ImageClip
import numpy as np

def apply_ken_burns(image_path, duration=5, fps=24, size=(1280, 720), zoom_ratio=1.2, direction="random"):
    """
    Applies a smooth Ken Burns effect (zoom + pan) to an image.
    Uses MoviePy v2.x syntax.
    """
    clip = ImageClip(image_path).with_duration(duration).with_fps(fps)
    
    # Target dimensions
    w, h = size
    
    # Direction logic
    import random
    if direction == "random":
        direction = random.choice(["zoom_in", "zoom_out", "pan_left", "pan_right"])
        
    def get_frame(get_frame_func, t):
        frame = get_frame_func(t)
        # Simple zoom calculation
        if direction == "zoom_in":
            factor = 1 + (zoom_ratio - 1) * (t / duration)
        elif direction == "zoom_out":
            factor = zoom_ratio - (zoom_ratio - 1) * (t / duration)
        else:
            factor = zoom_ratio # Static zoom for panning
            
        # Resize frame manually using numpy (since clip.resize might be tricky in v2.x without extra deps)
        from PIL import Image
        img = Image.fromarray(frame)
        
        # New size logic
        new_w = int(img.width * factor)
        new_h = int(img.height * factor)
        
        # Avoid zero or negative size
        new_w = max(1, new_w)
        new_h = max(1, new_h)
        
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Cropping/Panning logic
        # For zoom_in/out, we center crop
        # For panning, we slide the crop window
        
        left = (img_resized.width - w) / 2
        top = (img_resized.height - h) / 2
        
        if direction == "pan_left":
            shift = (img_resized.width - w) * (t / duration)
            left = shift
        elif direction == "pan_right":
            shift = (img_resized.width - w) * (1 - t / duration)
            left = shift
            
        # Ensure bounds
        left = max(0, min(left, img_resized.width - w))
        top = max(0, min(top, img_resized.height - h))
        
        img_final = img_resized.crop((left, top, left + w, top + h))
        return np.array(img_final)

    # Note: transformation in MoviePy v2 is slightly different but image_transform works
    return clip.transform(get_frame)

if __name__ == "__main__":
    import os
    # Placeholder for test run
    print("Ken Burns module ready. Run from composer or main pipeline.")
