import psycopg2
import sys

# Configuration
DB_HOST = "127.0.0.1"
DB_NAME = "antigravity"
DB_USER = "n8n"
DB_PASS = "n8n"
DB_PORT = "5432"

USER_ID = "9ce814df-9c1e-4de0-b92e-84c819b9fa00"

def check_query():
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
        
        print(f"🔍 Running query for user: {USER_ID}")
        
        # 1. Check Dashboard Query (get-jobs)
        print("\n=== Checking Dashboard Query (get-jobs) ===")
        dashboard_query = """
          SELECT id, source_video_url as source_url, project_status as status, progress, created_at, title, thumbnail_url, estimated_time_remaining 
          FROM projects 
          WHERE user_id = %s
          ORDER BY created_at DESC 
          LIMIT 20
        """
        cur.execute(dashboard_query, (USER_ID,))
        projects = cur.fetchall()
        print(f"📊 Dashboard found {len(projects)} projects")
        project_id = None
        for p in projects:
            print(f"  - Project: {p}")
            if 'Import' in p[5]: # Title
                project_id = p[0]

        if not project_id and len(projects) > 0:
            project_id = projects[0][0]

        if project_id:
            # 2. Check Studio Query (get-job)
            print(f"\n=== Checking Studio Query (get-job) for Project {project_id} ===")
            studio_query = """
                SELECT 
                    id, project_id, start_time, end_time, virality_score,
                    transcript_json, video_path, created_at,
                    COALESCE(title_generated, 'Clip sin título') as title,
                    COALESCE(description_generated, '') as hook_description,
                    '' as payoff_description,
                    'viral' as category,
                    ROW_NUMBER() OVER (ORDER BY created_at ASC) as rank,
                    COALESCE(hashtags, ARRAY[]::text[]) as hashtags,
                    render_status, render_progress, render_error
                FROM clips 
                WHERE project_id = %s 
                ORDER BY created_at ASC
            """
            cur.execute(studio_query, (project_id,))
            clips = cur.fetchall()
            print(f"📊 Studio found {len(clips)} clips")
            for c in clips:
                print(f"  - Clip: ID={c[0]}, Title={c[8]}")
                
            # 3. Check video_versions for the first clip
            if len(clips) > 0:
                clip_id = clips[0][0]
                print(f"\n=== Checking Video Version for Clip {clip_id} ===")
                vv_query = """
                    SELECT vv.file_path 
                    FROM video_versions vv
                    WHERE vv.clip_id = %s AND vv.version = 'preview'
                """
                cur.execute(vv_query, (clip_id,))
                ver = cur.fetchone()
                print(f"  - File Path: {ver}")
                
        else:
            print("❌ No project found to test studio query.")

        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_query()
