"""
Script to insert the generated viral clip into the web app's database
so it appears in the Studio view.
"""
import psycopg2
import uuid
import os
import shutil
import json
from datetime import datetime

# Database connection
conn = psycopg2.connect(user='n8n', password='n8n', host='127.0.0.1', port=5432, database='antigravity')
cur = conn.cursor()

# Check video_versions table exists
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'video_versions' ORDER BY ordinal_position")
vv_cols = cur.fetchall()
print("=== VIDEO_VERSIONS COLUMNS ===")
for c in vv_cols:
    print(f"  {c[0]:30s} {c[1]}")

# Existing user ID from the projects
USER_ID = 'e7b33fe8-2a49-45be-99c8-181d064d5e1b'

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(PROJECT_ROOT, 'app', '.env')
load_dotenv(env_path)
STORAGE_BASE = os.path.join(PROJECT_ROOT, 'app', 'storage')

# Create storage directories
for d in ['source', 'processed', 'subtitled', 'temp']:
    os.makedirs(os.path.join(STORAGE_BASE, d), exist_ok=True)

# Generate UUIDs
project_id = str(uuid.uuid4())
clip_id = str(uuid.uuid4())

print(f"\nProject ID: {project_id}")
print(f"Clip ID:    {clip_id}")

# 1. Create project entry
cur.execute("""
    INSERT INTO projects (id, user_id, source_video_url, title, project_status, progress, created_at, updated_at)
    VALUES (%s, %s, %s, %s, 'COMPLETED', 100, NOW(), NOW())
""", (project_id, USER_ID, 'https://youtu.be/mJvNIAxZj2U', 'ELEFANTES: ¡LO QUE NADIE TE DIJO!'))
print("✅ Project created")

# 2. Copy source video to storage
source_video_src = os.path.join(OUTPUT_DIR, 'source_video.mp4')
source_video_dst = os.path.join(STORAGE_BASE, 'source', f'{project_id}.mp4')
if os.path.exists(source_video_src):
    shutil.copy2(source_video_src, source_video_dst)
    print(f"✅ Source video copied to: {source_video_dst}")

# 3. Find the generated viral clip
viral_clips = [f for f in os.listdir(OUTPUT_DIR) if f.startswith('VIRAL_')]
print(f"\nFound viral clips: {viral_clips}")

if viral_clips:
    clip_file = viral_clips[0]
    clip_src = os.path.join(OUTPUT_DIR, clip_file)
    
    # Copy clip to processed storage
    clip_dst = os.path.join(STORAGE_BASE, 'processed', f'{clip_id}.mp4')
    shutil.copy2(clip_src, clip_dst)
    print(f"✅ Clip copied to: {clip_dst}")
    
    # Also copy as subtitled version (since it already has subtitles burned in)
    subtitled_dst = os.path.join(STORAGE_BASE, 'subtitled', f'{clip_id}.mp4')
    shutil.copy2(clip_src, subtitled_dst)
    print(f"✅ Subtitled version copied to: {subtitled_dst}")
    
    # 4. Insert clip into clips table
    cur.execute("""
        INSERT INTO clips (id, project_id, start_time, end_time, virality_score, video_path, 
                          title_generated, description_generated, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
    """, (
        clip_id, project_id, 
        0.40, 18.58,  # start and end times from the pipeline
        92,  # virality score
        clip_dst,  # absolute path to the clip
        'ELEFANTES: ¡LO QUE NADIE TE DIJO!',
        'Descubre los datos más sorprendentes sobre los elefantes que nadie conoce. Video viral generado con IA.',
    ))
    print("✅ Clip inserted into DB")
    
    # 5. Insert video_versions entry for proxy-video streaming
    if vv_cols:
        try:
            cur.execute("""
                INSERT INTO video_versions (id, clip_id, version, file_path, created_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (str(uuid.uuid4()), clip_id, 'preview', clip_dst))
            print("✅ Video version (preview) created")
        except Exception as e:
            print(f"⚠️ Video versions insert failed (maybe different schema): {e}")
            conn.rollback()
            # Re-do previous inserts since we rolled back
            conn = psycopg2.connect(user='n8n', password='n8n', host='127.0.0.1', port=5432, database='antigravity')
            cur = conn.cursor()
            # Just commit without video_versions
            cur.execute("""
                INSERT INTO projects (id, user_id, source_video_url, title, project_status, progress, created_at, updated_at)
                VALUES (%s, %s, %s, %s, 'COMPLETED', 100, NOW(), NOW())
            """, (project_id, USER_ID, 'https://youtu.be/mJvNIAxZj2U', 'ELEFANTES: ¡LO QUE NADIE TE DIJO!'))
            cur.execute("""
                INSERT INTO clips (id, project_id, start_time, end_time, virality_score, video_path, 
                                  title_generated, description_generated, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
            """, (clip_id, project_id, 0.40, 18.58, 92, clip_dst,
                  'ELEFANTES: ¡LO QUE NADIE TE DIJO!',
                  'Descubre los datos más sorprendentes sobre los elefantes que nadie conoce.'))

conn.commit()
print(f"\n🎉 DONE! Go to: http://localhost:3000/studio/{project_id}")

conn.close()
