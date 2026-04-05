import psycopg2

# Configuration
DB_HOST = "127.0.0.1"
DB_NAME = "antigravity"
DB_USER = "n8n"
DB_PASS = "n8n"
DB_PORT = "5432"

VIDEO_ID = "tDHPVc1lzAQ"

def check_project():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()
        
        cur.execute("SELECT title, id, user_id FROM projects WHERE title LIKE %s", (f"%{VIDEO_ID}%",))
        projs = cur.fetchall()
        
        print(f"Found {len(projs)} projects for {VIDEO_ID}:")
        for p in projs:
            print(f"Project: {p[0]}")
            print(f"  ID: {p[1]}")
            print(f"  User: {p[2]}")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_project()
