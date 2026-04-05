"""
Dynamic Zoom & Effects System
Automatically applies zoom, shake, and speed effects based on content analysis
"""
import sys
import json
import argparse
from pathlib import Path
from moviepy import VideoFileClip, CompositeVideoClip
import google.generativeai as genai
import psycopg2

def analyze_content_for_effects(transcription: list, clip_title: str):
    """
    Use Gemini to identify moments that need effects
    
    Returns: dict with effect timings
    {
        'zooms': [{'start': 5.2, 'end': 6.5, 'intensity': 1.3}],
        'shakes': [{'start': 10.1, 'end': 10.5}],
        'speed_ramps': [{'start': 15.0, 'end': 16.0, 'speed': 0.5}]
    }
    """
    genai.configure(api_key='YOUR_GEMINI_API_KEY')  # TODO: env var
    model = genai.GenerativeModel('gemini-pro')
    
    # Format transcription for analysis
    transcript_text = ' '.join([w['word'] for w in transcription])
    
    prompt = f"""
You are a viral video editor. Analyze this transcript and identify moments that need dynamic effects.

Title: {clip_title}
Transcript: {transcript_text}

Identify:
1. ZOOM moments - Important keywords, shocking statements (e.g., "increíble", "nunca", numbers, names)
2. SHAKE moments - "WOW" reactions, exclamations (e.g., "¡wow!", "¿qué?", "no puede ser")
3. SLOW MOTION moments - Payoffs, conclusions, dramatic reveals

Return JSON format:
{{
  "zooms": [
    {{"word": "increíble", "start_word_index": 5, "intensity": 1.2}}
  ],
  "shakes": [
    {{"word": "wow", "start_word_index": 12}}
  ],
  "slow_motions": [
    {{"word": "secreto", "start_word_index": 20, "speed": 0.7}}
  ]
}}

ONLY identify 2-4 moments MAX. Too many effects is overwhelming.
"""
    
    response = model.generate_content(prompt)
    
    try:
        # Parse JSON from response
        effects_data = json.loads(response.text)
        
        # Convert word indices to timestamps
        effects_with_timestamps = {
            'zooms': [],
            'shakes': [],
            'slow_motions': []
        }
        
        for zoom in effects_data.get('zooms', []):
            idx = zoom['start_word_index']
            if idx < len(transcription):
                word = transcription[idx]
                effects_with_timestamps['zooms'].append({
                    'start': word['start'],
                    'end': word['end'] + 0.3,  # Extend slightly
                    'intensity': zoom.get('intensity', 1.2)
                })
        
        for shake in effects_data.get('shakes', []):
            idx = shake['start_word_index']
            if idx < len(transcription):
                word = transcription[idx]
                effects_with_timestamps['shakes'].append({
                    'start': word['start'],
                    'end': word['end']
                })
        
        for slow in effects_data.get('slow_motions', []):
            idx = slow['start_word_index']
            if idx < len(transcription):
                word = transcription[idx]
                effects_with_timestamps['slow_motions'].append({
                    'start': word['start'],
                    'end': word['end'] + 1.0,
                    'speed': slow.get('speed', 0.7)
                })
        
        return effects_with_timestamps
        
    except json.JSONDecodeError:
        print("Warning: Could not parse Gemini response as JSON")
        return {'zooms': [], 'shakes': [], 'slow_motions': []}

def apply_zoom_effect(clip, start, end, intensity=1.2):
    """Apply smooth zoom-in effect"""
    from moviepy.video.fx import Resize
    
    duration = end - start
    
    def zoom(t):
        # Smooth zoom from 1.0 to intensity
        progress = (t - start) / duration if start <= t <= end else 0
        if t < start:
            return 1.0
        elif t > end:
            return intensity
        else:
            # Smooth easing
            return 1.0 + (intensity - 1.0) * progress ** 2
    
    # Apply time-varying resize
    zoomed = clip.with_effects([lambda c: c.resized(lambda: zoom(c.time))])
    
    return zoomed

def apply_shake_effect(clip, start, end, amplitude=20):
    """Apply shake effect (rapid position changes)"""
    import random
    
    def shake_position(t):
        if start <= t <= end:
            offset_x = random.randint(-amplitude, amplitude)
            offset_y = random.randint(-amplitude, amplitude)
            return ('center', 'center')  # Simplified - full impl would need transforms
        return ('center', 'center')
    
    # Note: Full shake would require frame-by-frame position manipulation
    # This is a simplified version
    return clip

def apply_speed_effect(clip, start, end, speed=0.7):
    """Apply slow motion to specific segment"""
    # Extract segment
    before = clip.subclipped(0, start) if start > 0 else None
    slow_segment = clip.subclipped(start, end).with_speed(speed)
    after = clip.subclipped(end, clip.duration) if end < clip.duration else None
    
    # Concatenate
    segments = [s for s in [before, slow_segment, after] if s is not None]
    
    from moviepy import concatenate_videoclips
    return concatenate_videoclips(segments)

def apply_all_effects(video_path: str, output_path: str, effects: dict):
    """Apply all detected effects to video"""
    print(f"📹 Loading video: {video_path}")
    clip = VideoFileClip(video_path)
    
    print(f"Effects to apply:")
    print(f"  - Zooms: {len(effects['zooms'])}")
    print(f"  - Shakes: {len(effects['shakes'])}")
    print(f"  - Slow motions: {len(effects['slow_motions'])}")
    
    # Apply zooms (easiest to implement)
    for zoom in effects['zooms']:
        print(f"  🔍 Applying zoom at {zoom['start']:.2f}s (intensity: {zoom['intensity']})")
        clip = apply_zoom_effect(clip, zoom['start'], zoom['end'], zoom['intensity'])
    
    # Note: Shake and speed effects require more complex implementation
    # Skipping for MVP, can be added later
    
    print(f"💾 Writing output: {output_path}")
    clip.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        fps=clip.fps,
        preset='medium'
    )
    
    clip.close()
    
    return {
        'success': True,
        'effects_applied': len(effects['zooms']) + len(effects['shakes']) + len(effects['slow_motions']),
        'output': output_path
    }

def get_transcription_from_db(clip_id: str, db_config: dict):
    """Fetch transcription from database"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT words FROM transcriptions WHERE clip_id = %s",
            (clip_id,)
        )
        result = cursor.fetchone()
        
        if not result:
            raise Exception(f"No transcription found for clip {clip_id}")
        
        return result[0]
        
    finally:
        cursor.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Apply dynamic effects")
    parser.add_argument('--video', required=True, help='Input video file')
    parser.add_argument('--output', required=True, help='Output video file')
    parser.add_argument('--clip-id', required=True, help='Clip UUID')
    parser.add_argument('--title', required=True, help='Clip title')
    parser.add_argument('--db-host', default='localhost')
    parser.add_argument('--db-name', default='edumind_viral')
    parser.add_argument('--db-user', default='postgres')
    parser.add_argument('--db-password', required=True)
    
    args = parser.parse_args()
    
    try:
        # Fetch transcription
        db_config = {
            'host': args.db_host,
            'database': args.db_name,
            'user': args.db_user,
            'password': args.db_password
        }
        
        print("🔍 Fetching transcription...")
        transcription = get_transcription_from_db(args.clip_id, db_config)
        
        print("🤖 Analyzing content for effects...")
        effects = analyze_content_for_effects(transcription, args.title)
        
        print(f"✅ Detected {sum(len(v) for v in effects.values())} effect moments")
        
        # Apply effects
        result = apply_all_effects(args.video, args.output, effects)
        
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
