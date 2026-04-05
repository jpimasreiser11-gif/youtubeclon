import psycopg2
import sys
import os

def check_subtitle_preconditions(clip_id):
    results = {}
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="antigravity",
            user="n8n",
            password="n8n"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version(), current_database(), current_user")
        v, db, user = cursor.fetchone()
        print(f"DEBUG (System Python): Connected to {db} as {user} on {v}")
        
        # 1. Check Database (Clips table)
        print(f"--- Checking Database for Clip ID: {clip_id} ---")
        cursor.execute("""
            SELECT transcription_status, transcript_json, project_id 
            FROM clips 
            WHERE id = %s
        """, (clip_id,))
        clip_data = cursor.fetchone()
        
        if not clip_data:
            print(f"❌ Clip {clip_id} not found in database clips table.")
        else:
            status, transcript_json, project_id = clip_data
            print(f"✅ Clip found in clips table.")
            print(f"   Transcription Status: {status}")
            print(f"   Has transcript_json: {transcript_json is not None}")
        
        # 1b. Check Transcriptions table
        cursor.execute("""
            SELECT id, words FROM transcriptions WHERE clip_id = %s
        """, (clip_id,))
        trans_data = cursor.fetchone()
        
        if trans_data:
            print(f"✅ Found entry in transcriptions table.")
            print(f"   Record ID: {trans_data[0]}")
            print(f"   Has words: {trans_data[1] is not None}")
        else:
            print(f"❌ Transcription record MISSING in transcriptions table.")
        
        # 2. Check File System
        print(f"\n--- Checking File System ---")
        base_dir = r"app\storage"
        clip_path = os.path.join(base_dir, "clips", f"{clip_id}.mp4")
        
        if os.path.exists(clip_path):
            print(f"✅ Clip file exists at: {clip_path}")
            print(f"   Size: {os.path.getsize(clip_path)} bytes")
        else:
            print(f"❌ Clip file MISSING at: {clip_path}")
            
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_subtitle_preconditions("44c605f9-882e-4bc8-b82a-9a101299b452")
