import psycopg2
conn = psycopg2.connect(user='n8n', password='n8n', host='127.0.0.1', port=5432, database='antigravity')
cur = conn.cursor()

# Find the project we created for the elephant video
cur.execute("SELECT id, title, project_status FROM projects WHERE source_video_url LIKE '%mJvNIAxZj2U%'")
projects = cur.fetchall()
print("Projects for this video:")
for p in projects:
    print(f"  ID: {p[0]}, Title: {p[1]}, Status: {p[2]}")
    
    # Find clips for this project
    cur.execute("SELECT id, start_time, end_time, virality_score, video_path, title_generated FROM clips WHERE project_id = %s", (p[0],))
    clips = cur.fetchall()
    for c in clips:
        print(f"    Clip: {c[0]}, {c[1]}s-{c[2]}s, Score: {c[3]}, Title: {c[5]}")
        print(f"    Path: {c[4]}")
        
        # Check video_versions
        cur.execute("SELECT id, version, file_path FROM video_versions WHERE clip_id = %s", (c[0],))
        versions = cur.fetchall()
        for v in versions:
            print(f"    Version: {v[1]}, Path: {v[2]}")
            import os
            print(f"    File exists: {os.path.exists(v[2]) if v[2] else False}")

conn.close()
