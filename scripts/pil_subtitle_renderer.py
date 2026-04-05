"""
PIL-based subtitle renderer for video clips
Reliable alternative to MoviePy TextClip that works without ImageMagick
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os
import sys

# FIX: Forzar UTF-8 en Windows para evitar UnicodeEncodeError con emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Default font settings
DEFAULT_FONT_SIZE = 80
DEFAULT_COLOR = (255, 255, 0)  # Yellow
DEFAULT_STROKE_COLOR = (0, 0, 0)  # Black
DEFAULT_STROKE_WIDTH = 3

# Style Presets
STYLES = {
    "DEFAULT": {
        "font_size": 100,
        "color": (255, 255, 255), # White
        "stroke_color": (0, 0, 0),
        "stroke_width": 8,
        "uppercase": True,
        "bg_color": None
    },
    "HORMOZI": {
        "font_size": 130, # Even bigger for impact
        "color": (255, 255, 255), # White base
        "stroke_color": (0, 0, 0),
        "stroke_width": 10, # Thick outline
        "uppercase": True,
        "bg_color": None, # Remove background as requested
        "highlight_color": (0, 255, 0) # Bright Green
    },
    "MINIMALIST": {
        "font_size": 60,
        "color": (255, 255, 255), # White
        "stroke_color": (0, 0, 0),
        "stroke_width": 2,
        "uppercase": False,
        "bg_color": None
    }
}

# Speaker Color Palette (Enterprise)
SPEAKER_COLORS = {
    "SPEAKER_0": (255, 255, 0),   # Yellow
    "SPEAKER_1": (0, 255, 255),   # Cyan
    "SPEAKER_2": (255, 128, 0),   # Orange
    "SPEAKER_3": (0, 255, 0),     # Green
}

def get_font(font_size=DEFAULT_FONT_SIZE):
    """
    Get TrueType font, with fallback options
    """
    # Try to load Arial Bold (common on Windows)
    font_paths = [
        "C:/Windows/Fonts/arialbd.ttf",  # Windows Arial Bold
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Linux
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, font_size)
            except:
                continue
    
    # Fallback to default PIL font
    print(f"  Warning: Could not load TrueType font, using default")
    return ImageFont.load_default()


def create_text_image(text, font_size=DEFAULT_FONT_SIZE, color=DEFAULT_COLOR, 
                     stroke_color=DEFAULT_STROKE_COLOR, stroke_width=DEFAULT_STROKE_WIDTH,
                     max_width=1080):
    """
    Create a PIL Image with styled text (yellow with black stroke)
    
    Args:
        text: Text to render
        font_size: Font size in pixels
        color: RGB tuple for text color
        stroke_color: RGB tuple for stroke/outline color
        stroke_width: Width of text outline
        max_width: Maximum width for text wrapping
    
    Returns:
        PIL Image with transparent background and styled text
    """
    font = get_font(font_size)
    
    # Create a temporary image to calculate text size
    temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp_img)
    
    # Get text bounding box (includes stroke)
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Add padding
    padding = 20
    img_width = text_width + padding * 2
    img_height = text_height + padding * 2
    
    # Create actual image with transparency
    img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw text with stroke (outline)
    text_position = (padding, padding)
    draw.text(
        text_position,
        text,
        font=font,
        fill=color + (255,),  # Add alpha channel (opaque)
        stroke_width=stroke_width,
        stroke_fill=stroke_color + (255,)
    )
    
    return img


    return img


def create_styled_text_image(text, style_name="DEFAULT", custom_color=None):
    """
    Create a PIL Image based on a style preset
    """
    style = STYLES.get(style_name, STYLES["DEFAULT"])
    text_color = custom_color if custom_color else style["color"]
    
    # Process text
    if style.get("uppercase"):
        text = text.upper()
    
    font = get_font(style["font_size"])
    
    # Create temp image for size
    temp_img = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp_img)
    
    bbox = draw.textbbox((0, 0), text, font=font, stroke_width=style["stroke_width"])
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    padding = 30
    img_width = text_width + padding * 2
    img_height = text_height + padding * 2
    
    img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    if style.get("bg_color"):
        # Draw rounded rectangle background
        draw.rounded_rectangle([10, 10, img_width-10, img_height-10], radius=15, fill=style["bg_color"])

    draw.text(
        (padding, padding),
        text,
        font=font,
        fill=text_color + (255,),
        stroke_width=style["stroke_width"],
        stroke_fill=style["stroke_color"] + (255,)
    )
    
    return img


def get_active_words(words, current_time):
    """
    Get words that should be visible at the current timestamp
    
    Args:
        words: List of word dicts with 'word', 'start', 'end' keys
        current_time: Current time in seconds
    
    Returns:
        List of words that are active at current_time
    """
    active = []
    for word_data in words:
        start = word_data['start']
        end = word_data['end']
        
        # Word is active if current_time falls within its duration
        if start <= current_time < end:
            active.append(word_data)
    
    return active


def render_subtitles_on_frame(frame_array, words, current_time, video_size, style_name="DEFAULT"):
    """
    Overlay subtitles on a single video frame with styling
    New: Support for word highlighting in block-based captions
    """
    active_words = get_active_words(words, current_time)
    
    if not active_words:
        return frame_array
        
    # FIX "DOBLES": If multiple words are active, only take the most specific one 
    # (the one with the latest start time or the one that just started)
    # This prevents overlapping phrases and individual words on top of each other.
    if len(active_words) > 1:
        # Sort by start time descending (latest first)
        active_words = [sorted(active_words, key=lambda x: x['start'], reverse=True)[0]]
    
    frame_img = Image.fromarray(frame_array.astype('uint8'), 'RGB')
    w, h = video_size
    style = STYLES.get(style_name, STYLES["DEFAULT"])
    
    # We render all words that belong to the same "chunk" at once
    # For now, we take the active words and their immediate neighbors to form a phrase
    
    for word_data in active_words:
        word_text = word_data['word'].strip()
        
        # Hormozi Pop Effect logic: 
        duration = word_data['end'] - word_data['start']
        elapsed = current_time - word_data['start']
        progress = elapsed / duration if duration > 0 else 0
        
        # Highlight logic
        is_highlighted = (style_name == "HORMOZI")
        text_color = style["highlight_color"] if is_highlighted else style["color"]
        
        # Style selection
        text_img = create_styled_text_image(word_text, style_name, text_color)
        
        # Apply scaling "Pop"
        if style_name == "HORMOZI":
            # Elastic easing out for impact
            if progress < 0.2:
                scale = 0.8 + np.sin(progress * (np.pi / 0.2)) * 0.4 # Quick pop to 1.2
            else:
                scale = 1.0
                
            nw, nh = int(text_img.width * scale), int(text_img.height * scale)
            text_img = text_img.resize((nw, nh), Image.Resampling.LANCZOS)

        text_width, text_height = text_img.size
        x_position = (w - text_width) // 2
        y_position = int(h * 0.65) # Adjusted position
        
        frame_img.paste(text_img, (x_position, y_position), text_img)
    
    return np.array(frame_img)


def create_subtitle_renderer(words, video_size):
    """
    Create a make_frame function for MoviePy that includes subtitle rendering
    
    Args:
        words: List of word dicts with timestamps
        video_size: Tuple of (width, height)
    
    Returns:
        Function that takes (get_frame, t) and returns frame with subtitles
    """
    def make_frame_with_subtitles(get_frame, t):
        """
        MoviePy make_frame wrapper that adds subtitles
        
        Args:
            get_frame: Original video's get_frame function
            t: Current time in seconds
        
        Returns:
            Frame with subtitles as numpy array
        """
        # Get original frame
        frame = get_frame(t)
        
        # Add subtitles
        return render_subtitles_on_frame(frame, words, t, video_size)
    
    return make_frame_with_subtitles


# Test function
if __name__ == "__main__":
    print("Testing PIL subtitle renderer...")
    
    # Test text image creation
    test_img = create_text_image("TESTING", font_size=100)
    test_output = "output/test_text.png"
    os.makedirs("output", exist_ok=True)
    test_img.save(test_output)
    print(f"Created test image: {test_output}")
    
    # Test word filtering
    test_words = [
        {"word": "Hello", "start": 0.0, "end": 0.5},
        {"word": "World", "start": 0.5, "end": 1.0},
        {"word": "Test", "start": 1.0, "end": 1.5},
    ]
    
    active = get_active_words(test_words, 0.3)
    print(f"Active words at 0.3s: {[w['word'] for w in active]}")
    
    active = get_active_words(test_words, 0.7)
    print(f"Active words at 0.7s: {[w['word'] for w in active]}")
    
    print("\nPIL renderer module is ready!")
