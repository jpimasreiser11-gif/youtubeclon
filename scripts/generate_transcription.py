"""
Generate word-level transcription using OpenAI Whisper
Saves to database for editing in Studio
"""
import sys
import json
import argparse
from pathlib import Path
import whisper
import psycopg2
from datetime import datetime

def extract_audio_segment(video_path: str, start_time: float, end_time: float, output_path: str):
    """Extract audio from video clip"""
    import subprocess
    
    duration = end_time - start_time
    cmd = [
        'ffmpeg', '-y',
        '-ss', str(start_time),
        '-i', video_path,
        '-t', str(duration),
        '-vn',  # No video
        '-acodec', 'pcm_s16le',
        '-ar', '16000',  # Whisper prefers 16kHz
        '-ac', '1',  # Mono
        output_path
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)

def transcribe_with_whisper(audio_path: str, model_size: str = "base", language: str = None):
    """
    Transcribe audio with word-level timestamps
    
    Args:
        audio_path: Path to audio file (WAV preferred)
        model_size: Whisper model (tiny/base/small/medium/large)
        language: Force language (None for auto-detect)
    
    Returns:
        dict with 'words' array and 'language'
    """
    print(f"Loading Whisper model: {model_size}...")
    model = whisper.load_model(model_size)
    
    print(f"Transcribing {audio_path}...")
    result = model.transcribe(
        audio_path,
        word_timestamps=True,  # CRITICAL for subtitle timing
        language=language,
        verbose=False
    )
    
    # Extract words from all segments
    all_words = []
    for segment in result.get('segments', []):
        for word_data in segment.get('words', []):
            all_words.append({
                'word': word_data['word'].strip(),
                'start': round(word_data['start'], 3),
                'end': round(word_data['end'], 3),
                'confidence': round(word_data.get('probability', 1.0), 3)
            })
    
    return {
        'words': all_words,
        'language': result.get('language', 'unknown'),
        'text': result.get('text', '')
    }

def save_to_database(clip_id: str, transcription: dict, db_config: dict):
    """Save transcription to PostgreSQL"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        # Insert or update transcription
        cursor.execute("""
            INSERT INTO transcriptions (clip_id, language, words, edited)
            VALUES (%s, %s, %s, false)
            ON CONFLICT (clip_id) 
            DO UPDATE SET 
                words = EXCLUDED.words,
                language = EXCLUDED.language,
                updated_at = NOW()
            RETURNING id
        """, (
            clip_id,
            transcription['language'],
            json.dumps(transcription['words'])
        ))
        
        transcription_id = cursor.fetchone()[0]
        
        # Update clip status
        cursor.execute("""
            UPDATE clips 
            SET transcription_status = 'completed'
            WHERE id = %s
        """, (clip_id,))
        
        conn.commit()
        print(f"✅ Transcription saved successfully (ID: {transcription_id})")
        return transcription_id
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Generate word-level transcription with Whisper")
    parser.add_argument('--video', required=True, help='Path to source video')
    parser.add_argument('--clip-id', required=True, help='Clip UUID')
    parser.add_argument('--start', type=float, required=True, help='Start time in seconds')
    parser.add_argument('--end', type=float, required=True, help='End time in seconds')
    parser.add_argument('--model', default='base', choices=['tiny', 'base', 'small', 'medium', 'large'], help='Whisper model size')
    parser.add_argument('--language', default=None, help='Force language (es, en, etc.)')
    parser.add_argument('--db-host', default='localhost')
    parser.add_argument('--db-name', default='edumind_viral')
    parser.add_argument('--db-user', default='postgres')
    parser.add_argument('--db-password', required=True)
    
    args = parser.parse_args()
    
    # Create temp directory for audio
    temp_dir = Path('temp_audio')
    temp_dir.mkdir(exist_ok=True)
    audio_path = temp_dir / f"{args.clip_id}.wav"
    
    try:
        # Step 1: Extract audio from clip segment
        print("📹 Extracting audio segment...")
        extract_audio_segment(args.video, args.start, args.end, str(audio_path))
        
        # Step 2: Transcribe with Whisper
        print("🎤 Transcribing with Whisper...")
        transcription = transcribe_with_whisper(
            str(audio_path),
            model_size=args.model,
            language=args.language
        )
        
        print(f"✅ Found {len(transcription['words'])} words")
        print(f"   Language: {transcription['language']}")
        
        # Step 3: Save to database
        print("💾 Saving to database...")
        db_config = {
            'host': args.db_host,
            'database': args.db_name,
            'user': args.db_user,
            'password': args.db_password
        }
        
        save_to_database(args.clip_id, transcription, db_config)
        
        # Output JSON for API response
        output = {
            'success': True,
            'clip_id': args.clip_id,
            'words_count': len(transcription['words']),
            'language': transcription['language']
        }
        print(json.dumps(output))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }), file=sys.stderr)
        sys.exit(1)
    finally:
        # Cleanup temp file
        if audio_path.exists():
            audio_path.unlink()

if __name__ == '__main__':
    main()
