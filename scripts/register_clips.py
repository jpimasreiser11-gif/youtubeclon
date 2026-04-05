import json
import psycopg2
import sys
import os
from datetime import datetime
import uuid

# Configuration
DB_HOST = "127.0.0.1"
DB_NAME = "antigravity"
DB_USER = "n8n"
DB_PASS = "n8n"
DB_PORT = "5432"

def register_clips(clipper_input_path, user_email_prefix="jpima"):
    print(f"🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    # 1. Load Clipper Input
    try:
        with open(clipper_input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            video_id = data['id']
            clips = data['clips']
            print(f"📂 Loaded {len(clips)} clips for video {video_id}")
    except Exception as e:
        print(f"❌ Failed to load input file: {e}")
        return

    # 2. Find User
    print(f"🔍 Finding user starting with '{user_email_prefix}'...")
    cur.execute("SELECT id, email FROM users WHERE email LIKE %s LIMIT 1", (f"{user_email_prefix}%",))
    user = cur.fetchone()
    
    if not user:
        print(f"❌ User not found!")
        return
    
    user_id, email = user
    print(f"👤 Found User: {email} ({user_id})")

    # 3. Find or Create Project
    # Check if source_video_url contains the video_id 
    cur.execute("SELECT id FROM projects WHERE source_video_url LIKE %s AND user_id = %s", (f"%{video_id}%", user_id))
    project = cur.fetchone()
    
    if project:
        project_id = project[0]
        print(f"✅ Project exists: {project_id}")
    else:
        print(f"🆕 Creating new project for {video_id}...")
        project_id = str(uuid.uuid4())
        # Columns: id, user_id, source_video_url, title, thumbnail_url, project_status, created_at, updated_at
        try:
            cur.execute("""
                INSERT INTO projects (id, user_id, title, project_status, source_video_url, thumbnail_url, created_at, updated_at)
                VALUES (%s, %s, %s, 'COMPLETED', %s, '', NOW(), NOW())
                RETURNING id
            """, (project_id, user_id, f"YouTube Import: {video_id}", f"https://youtube.com/watch?v={video_id}"))
            conn.commit()
        except Exception as e:
            print(f"❌ Error inserting project: {e}")
            if hasattr(e, 'pgerror'): print(e.pgerror)
            return

        project_row = cur.fetchone()
        if project_row:
             # fetchone returns a tuple if RETURNING is used
             # But we need to handle if it returns None? No, insert shoud return.
             pass
        print(f"✅ Project created: {project_id}")

    # 4. Insert Clips
    print(f"💾 Registering {len(clips)} clips...")
    inserted_count = 0
    
    for i, clip in enumerate(clips):
        clip_id = str(uuid.uuid4())
        title = clip.get('title', f"Clip {i+1}")
        start_time = clip['start_time']
        end_time = clip['end_time']
        duration = end_time - start_time
        
        # Check if clip already exists (by approx match)
        cur.execute("""
            SELECT id FROM clips 
            WHERE project_id = %s 
            AND ABS(start_time - %s) < 0.1 
            AND ABS(end_time - %s) < 0.1
        """, (project_id, start_time, end_time))
        
        if cur.fetchone():
            print(f"  ⚠️ Clip already exists: {title}. Deleting to re-register...")
            cur.execute("""
                SELECT id FROM clips 
                WHERE project_id = %s 
                AND ABS(start_time - %s) < 0.1 
                AND ABS(end_time - %s) < 0.1
            """, (project_id, start_time, end_time))
            existing_id = cur.fetchone()[0]
            # Delete video_versions first if not cascade
            cur.execute("DELETE FROM video_versions WHERE clip_id = %s", (existing_id,))
            cur.execute("DELETE FROM clips WHERE id = %s", (existing_id,))
            # continue # Don't continue, proceed to insert new

        # Insert
        try:
            cur.execute("""
                INSERT INTO clips (
                    id, project_id, title_generated, 
                    start_time, end_time, 
                    virality_score, 
                    transcription_status, render_status, render_progress,
                    created_at, auto_adjusted,
                    hook_description, payoff_description, description
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'completed', 'completed', 100, NOW(), true, %s, %s, %s)
            """, (
                clip_id, project_id, title, start_time, end_time, clip.get('score', 85),
                clip.get('hook', ''), clip.get('payoff', ''), clip.get('description', '')
            ))
            
            # Find the actual file
            # content title might not match filename exactly due to sanitization
            # We'll search for the largest mp4 file created recently or matching name
            # For this MVP, we assume the filename contains the title sanitized
            
            output_dir = os.path.abspath("output")
            file_path = None
            
            # Sanitization logic from clipper.py (approximate)
            safe_filename = "".join([c for c in title if c.isalnum() or c in (' ', '-', '_')]).strip()
            potential_path = os.path.join(output_dir, f"{safe_filename}.mp4")
            
            if os.path.exists(potential_path):
                file_path = potential_path
            else:
                # Fallback: search for any mp4 in output/ that contains part of the title
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        if file.endswith(".mp4") and (safe_filename in file or title[:10] in file):
                            file_path = os.path.join(root, file)
                            break
                    if file_path: break
            
            if not file_path:
                print(f"  ⚠️ File not found by name for '{title}'. Trying recent files in {output_dir}...")
                # Fallback 2: Look for the most recent mp4 file (modified in last 24 hours)
                base_time = os.path.getmtime(output_dir) if os.path.exists(output_dir) else 0
                recent_files = []
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        if file.endswith(".mp4"):
                            full_path = os.path.join(root, file)
                            mtime = os.path.getmtime(full_path)
                            age = datetime.now().timestamp() - mtime
                            # print(f"    Found candidate: {file} (age: {age:.0f}s)")
                            # If modified in last 24 hours
                            if age < 86400:
                                recent_files.append((full_path, mtime))
                
                if recent_files:
                    # Sort by time descending
                    recent_files.sort(key=lambda x: x[1], reverse=True)
                    file_path = recent_files[0][0]
                    print(f"  ⚡ Found recent file: {os.path.basename(file_path)}")
            
            if not file_path:
                print(f"  ❌ File absolutely not found for '{title}', skipping DB insertion")
                continue
                
            print(f"  📎 Linking to file: {file_path}")
            
            cur.execute("""
                INSERT INTO video_versions (id, clip_id, version, file_path, status, created_at)
                VALUES (%s, %s, 'preview', %s, 'COMPLETED', NOW())
            """, (str(uuid.uuid4()), clip_id, file_path))
            
            inserted_count += 1
            print(f"  ✅ Inserted: {title}")
            
        except Exception as e:
            print(f"  ❌ Error inserting clip {title}: {e}")
            conn.rollback()
            continue

    conn.commit()
    conn.close()
    print(f"🎉 Done! Registered {inserted_count} new clips.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python register_clips.py <path_to_clipper_input.json>")
        sys.exit(1)
        
    register_clips(sys.argv[1])
