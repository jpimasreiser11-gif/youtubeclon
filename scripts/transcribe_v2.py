import argparse
import json
import sys
import os
import torch
import psycopg2
from pathlib import Path
from faster_whisper import WhisperModel

# FIX: Forzar UTF-8 en Windows para evitar UnicodeEncodeError con emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def save_to_database(clip_id, transcription, db_config):
    """Save transcription to PostgreSQL"""
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Insert or update transcription record in 'transcriptions' table
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
        
        # Update clip status AND transcript_json in 'clips' table (for UI)
        cursor.execute("""
            UPDATE clips 
            SET transcription_status = 'completed',
                transcript_json = %s
            WHERE id = %s
        """, (json.dumps(transcription['words']), clip_id))
        
        conn.commit()
        print(f"✅ Transcription saved to DB (ID: {transcription_id})")
        return transcription_id
        
    except Exception as e:
        if 'conn' in locals(): conn.rollback()
        raise e
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

def transcribe_v2(input_file, clip_id, model_size="large-v3", device="cuda", compute_type="int8", db_config=None):
    """
    High-performance transcription using faster-whisper and DB integration.
    """
    try:
        # Check for CUDA availability
        actual_device = "cuda" if torch.cuda.is_available() and device == "cuda" else "cpu"
        print(f"🚀 Using device: {actual_device} with model: {model_size}")
        
        # Load model with quantization
        model = WhisperModel(model_size, device=actual_device, compute_type=compute_type)
        
        # Transcribe with word-level timestamps
        segments, info = model.transcribe(
            input_file, 
            word_timestamps=True, 
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        words_data = []
        for segment in segments:
            for word in segment.words:
                words_data.append({
                    "word": word.word.strip(),
                    "start": round(word.start, 3),
                    "end": round(word.end, 3),
                    "confidence": round(word.probability, 3)
                })
        
        transcription = {
            "language": info.language,
            "words": words_data,
            "text": "".join([s.text for s in segments]) # Reconstructed text
        }
        
        if db_config:
            save_to_database(clip_id, transcription, db_config)
            
        return {
            "status": "success",
            "metadata": {
                "language": info.language,
                "duration": round(info.duration, 2),
                "device": actual_device,
                "model": model_size,
                "word_count": len(words_data)
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sovereign Transcription Engine V2")
    parser.add_argument("--video", required=True, help="Input video file path")
    parser.add_argument("--clip-id", required=True, help="Clip UUID")
    parser.add_argument("--model", default="large-v3", help="Model size")
    parser.add_argument("--device", default="cuda", help="Target device")
    parser.add_argument("--db-host", default="127.0.0.1")
    parser.add_argument("--db-name", default="antigravity")
    parser.add_argument("--db-user", default="postgres")
    parser.add_argument("--db-password", required=True)
    
    args = parser.parse_args()
    
    db_config = {
        'host': args.db_host,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }
    
    result = transcribe_v2(args.video, args.clip_id, args.model, args.device, db_config=db_config)
    print(json.dumps(result, ensure_ascii=False))
