import psycopg2

# Configuration
DB_HOST = "127.0.0.1"
DB_NAME = "antigravity"
DB_USER = "n8n"
DB_PASS = "n8n"
DB_PORT = "5432"

# The user currently logged in on frontend (from debug_user.log)
CORRECT_USER_ID = "06038e52-625a-47cb-9158-4a5d405b2bd7"
VIDEO_ID = "tDHPVc1lzAQ"

def fix_ownership():
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
        
        print(f"🔄 Transferring project {VIDEO_ID} to user {CORRECT_USER_ID}...")
        
        # Check current owner
        cur.execute("SELECT id, user_id, title FROM projects WHERE source_video_url LIKE %s", (f"%{VIDEO_ID}%",))
        project = cur.fetchone()
        
        if not project:
            print("❌ Project not found!")
            return

        print(f"  Current Project: {project[0]}")
        print(f"  Current Owner: {project[1]}")
        
        if str(project[1]) == CORRECT_USER_ID:
            print("✅ Already owned by correct user.")
        else:
            cur.execute("""
                UPDATE projects 
                SET user_id = %s 
                WHERE id = %s
            """, (CORRECT_USER_ID, project[0]))
            conn.commit()
            print(f"✅ Transferred ownership to {CORRECT_USER_ID}")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_ownership()
