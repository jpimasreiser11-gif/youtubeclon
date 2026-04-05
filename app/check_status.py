import psycopg2

DB_CONFIG = {
    "user": "n8n",
    "password": "n8n",
    "host": "localhost",
    "port": 5432,
    "database": "antigravity"
}

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("Checking latest project...")
        # Get latest project
        cur.execute("""
            SELECT id, title, project_status, created_at 
            FROM projects 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        project = cur.fetchone()
        
        if not project:
            print("No projects found.")
            return

        proj_id, title, status, created_at = project
        print(f"Project ID: {proj_id}")
        print(f"Title: {title}")
        print(f"Status: {status}")
        # print(f"Error: {error}")
        
        # Count clips
        cur.execute("SELECT count(*) FROM clips WHERE project_id = %s", (str(proj_id),))
        clip_count = cur.fetchone()[0]
        print(f"Clip Count: {clip_count}")
        
        if clip_count > 0:
            print("\nClips found:")
            cur.execute("SELECT id, virality_score, created_at FROM clips WHERE project_id = %s", (str(proj_id),))
            for clip in cur.fetchall():
                print(f" - Clip {clip[0]} (Score: {clip[1]})")
        
        conn.close()
        
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    main()
