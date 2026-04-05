"""
AI Thumbnail Generator
Detects best frame with facial expression and adds viral text overlay
"""
import sys
import json
import argparse
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import google.generativeai as genai
import psycopg2

def load_video_frames(video_path: str, sample_rate: int = 30):
    """Extract frames from video at specified sample rate"""
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_indices = []
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    for i in range(0, total_frames, sample_rate):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, frame = cap.read()
        if ret:
            frames.append(frame)
            frame_indices.append(i / fps)  # Timestamp in seconds
    
    cap.release()
    return frames, frame_indices

def detect_faces(frame):
    """Detect faces in frame using Haar Cascade"""
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    return faces

def score_frame(frame):
    """
    Score frame based on:
    - Face size (bigger is better)
    - Contrast (more contrast = more emotion)
    - Brightness (not too dark/bright)
    """
    faces = detect_faces(frame)
    
    # Face score
    face_score = 0
    if len(faces) > 0:
        # Use largest face
        largest_face = max(faces, key=lambda f: f[2] * f[3])
        face_area = largest_face[2] * largest_face[3]
        total_area = frame.shape[0] * frame.shape[1]
        face_score = (face_area / total_area) * 100
    
    # Contrast score
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    contrast = gray.std()
    
    # Brightness score
    brightness = gray.mean()
    brightness_score = 100 - abs(brightness - 128) / 128 * 100
    
    # Combined score
    total_score = (face_score * 0.5) + (contrast * 0.3) + (brightness_score * 0.2)
    
    return total_score

def select_best_frame(frames):
    """Select frame with highest score"""
    scores = [score_frame(frame) for frame in frames]
    best_index = np.argmax(scores)
    return frames[best_index], best_index

def generate_viral_text(clip_title: str, category: str):
    """Generate viral thumbnail text using Gemini"""
    genai.configure(api_key='YOUR_GEMINI_API_KEY')  # TODO: Use env var
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
Generate a SHORT, ATTENTION-GRABBING text for a YouTube thumbnail.

Video Title: {clip_title}
Category: {category}

Rules:
- Maximum 5 words
- Use ALL CAPS
- Include emojis if relevant
- Be dramatic/clickbaity
- Create curiosity

Examples:
- "ESTO ES INCREÍBLE 🤯"
- "NO VAS A CREER ESTO"
- "SECRETO REVELADO 😱"

Generate thumbnail text:
"""
    
    response = model.generate_content(prompt)
    return response.text.strip()

def apply_enhancements(image: Image.Image):
    """Apply visual enhancements to make thumbnail pop"""
    # Increase saturation
    enhancer = ImageEnhance.Color(image)
    image = enhancer.enhance(1.3)
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.2)
    
    # Slight sharpness boost
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.1)
    
    return image

def add_text_overlay(image: Image.Image, text: str):
    """Add viral text overlay to thumbnail"""
    draw = ImageDraw.Draw(image)
    
    # Try to load custom font, fallback to default
    try:
        font = ImageFont.truetype("arial.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    # Get image dimensions
    width, height = image.size
    
    # Text position (top or bottom based on face location)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (width - text_width) // 2
    y = height - text_height - 50  # Bottom with padding
    
    # Draw text with outline
    outline_range = 3
    for adj_x in range(-outline_range, outline_range + 1):
        for adj_y in range(-outline_range, outline_range + 1):
            draw.text((x + adj_x, y + adj_y), text, font=font, fill='black')
    
    # Draw main text
    draw.text((x, y), text, font=font, fill='yellow')
    
    return image

def save_to_database(clip_id: str, thumbnail_path: str, viral_text: str, db_config: dict):
    """Save thumbnail metadata to database"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO thumbnails (clip_id, file_path, viral_text, created_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (clip_id) 
            DO UPDATE SET 
                file_path = EXCLUDED.file_path,
                viral_text = EXCLUDED.viral_text,
                updated_at = NOW()
            RETURNING id
        """, (clip_id, thumbnail_path, viral_text))
        
        thumbnail_id = cursor.fetchone()[0]
        conn.commit()
        
        return thumbnail_id
        
    finally:
        cursor.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Generate AI thumbnail")
    parser.add_argument('--video', required=True, help='Path to video file')
    parser.add_argument('--clip-id', required=True, help='Clip UUID')
    parser.add_argument('--title', required=True, help='Clip title')
    parser.add_argument('--category', default='general', help='Clip category')
    parser.add_argument('--output', required=True, help='Output thumbnail path')
    parser.add_argument('--db-host', default='localhost')
    parser.add_argument('--db-name', default='edumind_viral')
    parser.add_argument('--db-user', default='postgres')
    parser.add_argument('--db-password', required=True)
    
    args = parser.parse_args()
    
    try:
        print("📹 Loading video frames...")
        frames, timestamps = load_video_frames(args.video, sample_rate=30)
        
        print(f"✅ Extracted {len(frames)} frames")
        
        print("🔍 Analyzing frames for best thumbnail...")
        best_frame, best_index = select_best_frame(frames)
        
        print(f"🎯 Selected frame at {timestamps[best_index]:.2f}s")
        
        # Convert to PIL Image
        best_frame_rgb = cv2.cvtColor(best_frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(best_frame_rgb)
        
        # Resize to standard YouTube thumbnail size
        image = image.resize((1280, 720), Image.Resampling.LANCZOS)
        
        print("✨ Applying enhancements...")
        image = apply_enhancements(image)
        
        print("🤖 Generating viral text with Gemini...")
        viral_text = generate_viral_text(args.title, args.category)
        print(f"📝 Viral text: {viral_text}")
        
        print("🎨 Adding text overlay...")
        image = add_text_overlay(image, viral_text)
        
        # Save thumbnail
        image.save(args.output, 'JPEG', quality=95)
        print(f"💾 Saved thumbnail to: {args.output}")
        
        # Save to database
        db_config = {
            'host': args.db_host,
            'database': args.db_name,
            'user': args.db_user,
            'password': args.db_password
        }
        
        thumbnail_id = save_to_database(args.clip_id, args.output, viral_text, db_config)
        
        # Output JSON result
        result = {
            'success': True,
            'thumbnail_id': str(thumbnail_id),
            'thumbnail_path': args.output,
            'viral_text': viral_text,
            'selected_timestamp': timestamps[best_index]
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
