import argparse
import json
import sys
import os
import time
import subprocess
import psycopg2
import google.generativeai as genai
from pathlib import Path

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

def extract_audio(video_path, audio_path):
    """Extract audio from video file using FFmpeg"""
    print(f"🎵 Extracting audio from {video_path}...")
    try:
        command = [
            'ffmpeg', '-y', '-i', video_path,
            '-vn', '-acodec', 'libmp3lame', '-ab', '128k', '-ar', '44100',
            audio_path
        ]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error extracting audio: {e}")
        return False

def transcribe_with_gemini(input_file, api_key):
    """
    Transcribe using Gemini 2.0 Flash API.
    """
    genai.configure(api_key=api_key)
    
    # Extract audio if it's a video file
    is_video = input_file.lower().endswith(('.mp4', '.mkv', '.mov', '.avi'))
    file_to_upload = input_file
    
    if is_video:
        audio_path = input_file.rsplit('.', 1)[0] + "_temp.mp3"
        if extract_audio(input_file, audio_path):
            file_to_upload = audio_path
        else:
            print("⚠️ Transcription might be slower uploading original video file.")

    try:
        print(f"🚀 Uploading {file_to_upload} to Gemini File API...")
        uploaded_file = genai.upload_file(path=file_to_upload)
        
        # Wait for file to be processed (usually very fast for small files)
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(1)
            uploaded_file = genai.get_file(uploaded_file.name)
        
        if uploaded_file.state.name == "FAILED":
            raise Exception("Gemini File API processing failed.")

        print(f"🔍 Transcribing with Gemini 2.0 Flash...")
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        prompt = """
        Analyze this audio and provide a high-precision word-level transcription.
        You MUST respond ONLY with a JSON object in the following format:
        {
          "language": "es", 
          "words": [
            {
              "word": "Exact word",
              "start": 1.23, // Start time in seconds
              "end": 1.45,   // End time in seconds
              "confidence": 0.99
            }
          ]
        }
        Provide the transcription for the ENTIRE audio.
        """
        
        response = model.generate_content(
            [prompt, uploaded_file],
            generation_config={"response_mime_type": "application/json"}
        )
        
        # Cleanup uploaded file from Gemini
        genai.delete_file(uploaded_file.name)
        
        # Cleanup temp audio if created
        if is_video and os.path.exists(file_to_upload):
            os.remove(file_to_upload)
            
        try:
            transcription_data = json.loads(response.text)
            return transcription_data
        except json.JSONDecodeError:
            # Fallback if it didn't return perfect JSON
            print("❌ Gemini returned invalid JSON. Attempting to parse manually...")
            # Simple cleanup for common markdown block issues
            raw_text = response.text.strip()
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            return json.loads(raw_text)

    except Exception as e:
        # Cleanup
        if is_video and 'file_to_upload' in locals() and os.path.exists(file_to_upload) and file_to_upload != input_file:
            try: os.remove(file_to_upload)
            except: pass
        raise e

def main():
    parser = argparse.ArgumentParser(description="Flash Transcription Engine (Gemini 2.0)")
    parser.add_argument("--video", required=True, help="Input video/audio file path")
    parser.add_argument("--clip-id", required=True, help="Clip UUID")
    parser.add_argument("--db-host", default="127.0.0.1")
    parser.add_argument("--db-name", default="antigravity")
    parser.add_argument("--db-user", default="postgres")
    parser.add_argument("--db-password", required=True)
    parser.add_argument("--gemini-key", default=os.getenv("GEMINI_API_KEY"), help="Gemini API Key")
    
    args = parser.parse_args()
    
    if not args.gemini_key:
        print("❌ Error: GEMINI_API_KEY not found in environment or arguments.")
        sys.exit(1)
        
    db_config = {
        'host': args.db_host,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }
    
    try:
        # Start transcription
        transcription = transcribe_with_gemini(args.video, args.gemini_key)
        
        # Save to database
        save_to_database(args.clip_id, transcription, db_config)
        
        result = {
            "status": "success",
            "metadata": {
                "language": transcription.get('language', 'unknown'),
                "word_count": len(transcription.get('words', [])),
                "model": "gemini-2.0-flash"
            }
        }
        print(json.dumps(result, ensure_ascii=False))
        
    except Exception as e:
        result = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

if __name__ == "__main__":
    main()
