import os
import json
import shutil
import psycopg2
from dotenv import load_dotenv
import subprocess
import sys

# Load environment variables
load_dotenv('.env')

DB_CONFIG = {
    "user": os.getenv("POSTGRES_USER", "n8n"),
    "password": os.getenv("POSTGRES_PASSWORD", "n8n"),
    "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "antigravity")
}

def recover_project(project_id):
    temp_dir = f"storage/temp/{project_id}"
    if not os.path.exists(temp_dir):
        print(f"Error: Temp dir {temp_dir} not found")
        return

    # We need to find the clips. Since ingest.py didn't finish, we don't have the 'results' variable.
    # But we can infer it from the files or if there is a transcript somewhere.
    # Actually, ViralEngine.run_pipeline returns results. We lost it.
    # Let's try to reconstruct from the files in the directory.
    
    mp4_files = [f for f in os.listdir(temp_dir) if f.startswith('VIRAL_') and f.endswith('.mp4')]
    if not mp4_files:
        print("No viral clips found in temp dir")
        return

    print(f"Found {len(mp4_files)} clips to recover")
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        for filename in mp4_files:
            temp_path = os.path.join(temp_dir, filename)
            
            # Reconstruct basic metadata from filename or generic
            # In a real recovery we might want to re-run the analysis if we don't have the JSON,
            # but here we just want to save the work done.
            
            title = filename.replace('VIRAL_', '').replace('.mp4', '')
            
            # Insert clip
            cur.execute("""
                INSERT INTO clips (
                    project_id, start_time, end_time, virality_score, transcript_json, 
                    title_generated, description_generated, hook_description, payoff_description
                )
                VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                project_id, 
                0.0,
                30.0, # Dummy duration, we can get better via ffprobe if needed
                85,
                json.dumps([]),
                title,
                f"Recovered viral clip: {title}",
                "",
                ""
            ))
            
            clip_id = cur.fetchone()[0]
            
            # Move file
            final_path = os.path.join("storage/clips", f"{clip_id}.mp4")
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            shutil.move(temp_path, final_path)
            
            # Processed path
            processed_path = os.path.join("storage/processed", f"{clip_id}.mp4")
            os.makedirs(os.path.dirname(processed_path), exist_ok=True)
            shutil.copy2(final_path, processed_path)
            
            # Video version
            cur.execute("INSERT INTO video_versions (clip_id, version, file_path) VALUES (%s, 'preview', %s)", (clip_id, final_path))
            
            # Thumbnail
            thumb_path = os.path.join("storage/thumbnails", f"{clip_id}.jpg")
            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
            
            ffmpeg_exe = os.getenv("FFMPEG_PATH", "ffmpeg")
            subprocess.run([
                ffmpeg_exe, "-y",
                "-i", final_path, "-ss", "00:00:01", "-vframes", "1", thumb_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            cur.execute("INSERT INTO thumbnails (clip_id, url) VALUES (%s, %s)", (clip_id, thumb_path))
            
            print(f"✅ Recovered clip: {title} (ID: {clip_id})")

        # Update project status
        cur.execute("UPDATE projects SET project_status = 'COMPLETED', progress_percent = 100, current_step = '✅ Recuperado exitosamente' WHERE id = %s", (project_id,))
        conn.commit()
        print(f"🎉 Project {project_id} recovery COMPLETED")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Recovery failed: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        recover_project(sys.argv[1])
    else:
        print("Usage: python recover_project.py <project_id>")
