import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../app/.env'))

db_config = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': 'antigravity',
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'n8n')
}

clip_id = "24d43931-ffed-4911-a2a3-0455c71901c8"
dummy_words = [
    {"word": "This", "start": 0.0, "end": 0.5, "confidence": 0.99},
    {"word": "is", "start": 0.5, "end": 1.0, "confidence": 0.99},
    {"word": "a", "start": 1.0, "end": 1.5, "confidence": 0.99},
    {"word": "test", "start": 1.5, "end": 2.0, "confidence": 0.99}
]

try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    # Insert dummy
    cur.execute("""
        INSERT INTO transcriptions (clip_id, language, words, edited)
        VALUES (%s, 'en', %s, false)
        ON CONFLICT (clip_id) DO UPDATE 
        SET words = EXCLUDED.words
    """, (clip_id, json.dumps(dummy_words)))
    
    # Also update clips table for UI
    # cur.execute("""
    #     UPDATE clips 
    #     SET transcript_json = %s, transcription_status = 'completed'
    #     WHERE id = %s
    # """, (json.dumps(dummy_words), clip_id))
    
    conn.commit()
    print(f"✅ Dummy transcription inserted for {clip_id}")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error: {e}")
