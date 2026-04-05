import sys
import json
import argparse
from pathlib import Path
from moviepy import VideoFileClip
import psycopg2
import os
try:
    from proglog import ProgressBarLogger
except ImportError:
    # Fallback if proglog not strictly required or named differently
    class ProgressBarLogger:
        def __init__(self, *args, **kwargs): pass
        def __call__(self, *args, **kwargs): return self
        def log(self, *args, **kwargs): pass
        def on_bars_start(self, *args, **kwargs): pass
        def on_bars_update(self, *args, **kwargs): pass
        def on_message(self, *args, **kwargs): pass
        def iter_bar(self, iterable, *args, **kwargs): return iterable
        def bar_start(self, *args, **kwargs): pass
        def bar_stop(self, *args, **kwargs): pass
from dotenv import load_dotenv

# Load environment variables
root_dir = Path(__file__).parent.parent
env_path = root_dir / 'app' / '.env'
load_dotenv(dotenv_path=env_path)

# FIX: Forzar UTF-8 en Windows para evitar UnicodeEncodeError con emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import our custom PIL renderer
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pil_subtitle_renderer import render_subtitles_on_frame

def get_transcription_from_db(clip_id: str, db_config: dict):
    """Fetch transcription from database with robust matching and fallback"""
    print(f"🔍 Searching transcription for clip: {clip_id}")
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # 1. Try transcriptions table (Primary source) with text casting for robustness
        cursor.execute(
            "SELECT words FROM transcriptions WHERE clip_id::text = %s",
            (clip_id,)
        )
        result = cursor.fetchone()
        
        if result and result[0]:
            print("✅ Found words in 'transcriptions' table")
            return result[0]
            
        # 2. Try clips table (Fallback)
        print("⚠️ Not found in 'transcriptions', checking 'clips' table...")
        cursor.execute(
            "SELECT transcript_json FROM clips WHERE id::text = %s",
            (clip_id,)
        )
        result = cursor.fetchone()
        
        if result and result[0]:
            print("✅ Found words in 'clips' table")
            if isinstance(result[0], str):
                return json.loads(result[0])
            return result[0]
            
        # 3. Last resort manual scan in case of weird UUID issues
        print("🔍 performing manual scan of 'transcriptions' table...")
        cursor.execute("SELECT clip_id, words FROM transcriptions")
        for rid, rwords in cursor.fetchall():
            if str(rid).strip() == clip_id.strip():
                print(f"‼️ MANUAL MATCH FOUND for {clip_id}!")
                return rwords
                
        raise Exception(f"No transcription found for clip {clip_id} in tables 'transcriptions' or 'clips'")
        
    except Exception as e:
        print(f"❌ DB Error: {e}")
        raise
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

def set_render_status(clip_id: str, db_config: dict, status: str, progress: int = 0, error: str = None):
    """Helper to update render status in DB"""
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        if error:
            cur.execute(
                "UPDATE clips SET render_status = %s, render_progress = %s, render_error = %s WHERE id::text = %s",
                (status, progress, error, clip_id)
            )
        else:
            cur.execute(
                "UPDATE clips SET render_status = %s, render_progress = %s WHERE id::text = %s",
                (status, progress, clip_id)
            )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"⚠️ Failed to update DB status: {e}")

class RenderLogger(ProgressBarLogger):
    """Robust logger for MoviePy 1.0.3/proglog and DB updates"""
    def __init__(self, clip_id, db_config):
        super().__init__()
        self.clip_id = clip_id
        self.db_config = db_config
        self.last_p = -1

    def callback(self, **kwargs):
        """Standard proglog callback for general logging"""
        pass

    def on_bars_update(self, bar, values):
        # MoviePy 1.0.3 uses 'chunk' or 't' or 'index'
        if 'index' in values and 'total' in values:
            index = values['index']
            total = values['total']
            if total > 0:
                p = int((index / total) * 100)
                if p > self.last_p:
                    self.last_p = p
                    print(f"📈 Progress: {p}%")
                    # Update DB every 2% to give better feedback for long videos
                    if p % 2 == 0:
                        set_render_status(self.clip_id, self.db_config, 'processing', p)

def render_with_subtitles(video_path: str, output_path: str, words: list, clip_id: str, db_config: dict, style_name: str = 'DEFAULT'):
    """Main rendering function using PIL transform and progress reporting"""
    print(f"📹 Loading video: {video_path}")
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
        
    set_render_status(clip_id, db_config, 'processing', 0)
    
    clip = VideoFileClip(video_path)
    w, h = clip.size
    
    print(f"📊 Video size: {w}x{h}, Duration: {clip.duration}s")
    print(f"✨ Applying '{style_name}' subtitle style via PIL Renderer...")
    
    # Standardize style name
    style_map = {
        'tiktok': 'DEFAULT',
        'youtube': 'MINIMALIST',
        'minimal': 'MINIMALIST',
        'hormozi': 'HORMOZI',
        'default': 'DEFAULT',
        'clean': 'CLEAN'
    }
    final_style = style_map.get(style_name.lower(), style_name.upper())

    if final_style == 'CLEAN':
        print("✨ Style is CLEAN - Skipping subtitle rendering")
        final = clip
    else:
        def subtitle_frame_gen(get_frame, t):
            frame = get_frame(t)
            return render_subtitles_on_frame(frame, words, t, (w, h), style_name=final_style)

        final = clip.transform(subtitle_frame_gen)
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"💾 Writing to: {output_path}")
    
    # Defensive cleanup: Ensure output file is not locked or exists from failed run
    if os.path.exists(output_path):
        try:
            print(f"🧹 Removing existing file: {output_path}")
            os.remove(output_path)
        except Exception as e:
            print(f"⚠️ Warning: Could not remove existing file (it may be locked): {e}")
    
    logger = RenderLogger(clip_id, db_config)
    
    final.write_videofile(
        output_path,
        codec='libx264',
        audio_codec='aac',
        fps=clip.fps,
        preset='slow',
        threads=4,
        ffmpeg_params=['-crf', '18', '-profile:v', 'high', '-pix_fmt', 'yuv420p'],
        logger=logger
    )
    
    set_render_status(clip_id, db_config, 'completed', 100)
    print("✅ Rendering complete!")
    clip.close()
    final.close()
    
    return {
        'success': True,
        'output': output_path,
        'duration': clip.duration
    }

def main():
    parser = argparse.ArgumentParser(description="Render video with subtitles")
    parser.add_argument('--video', required=True, help='Input video file')
    parser.add_argument('--output', required=True, help='Output video file')
    parser.add_argument('--clip-id', required=True, help='Clip UUID for fetching transcription')
    parser.add_argument('--style', default='DEFAULT', help='Subtitle style')
    parser.add_argument('--db-host', default=os.getenv('POSTGRES_HOST', '127.0.0.1'))
    parser.add_argument('--db-name', default=os.getenv('POSTGRES_DB', 'antigravity'))
    parser.add_argument('--db-user', default=os.getenv('POSTGRES_USER', 'postgres'))
    parser.add_argument('--db-password', default=os.getenv('POSTGRES_PASSWORD', 'password'))
    
    args = parser.parse_args()
    
    try:
        db_config = {
            'host': args.db_host,
            'database': args.db_name,
            'user': args.db_user,
            'password': args.db_password
        }
        
        # Test connection and print identity
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("SELECT version(), current_database(), current_user")
        v, db, user = cur.fetchone()
        print(f"DEBUG: Connected to {db} as {user} on {v}")
        cur.close()
        conn.close()
        
        words = get_transcription_from_db(args.clip_id, db_config)
        
        if not words:
            raise Exception("No words in transcription")
        
        result = render_with_subtitles(args.video, args.output, words, args.clip_id, db_config, args.style)
        print(json.dumps(result))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
