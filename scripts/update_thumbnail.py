import psycopg2

# Configuration
DB_HOST = "127.0.0.1"
DB_NAME = "antigravity"
DB_USER = "n8n"
DB_PASS = "n8n"
DB_PORT = "5432"

VIDEO_ID = "tDHPVc1lzAQ"
THUMBNAIL_URL = f"https://img.youtube.com/vi/{VIDEO_ID}/maxresdefault.jpg"

def update_thumbnail():
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
        
        print(f"🖼️ Updating thumbnail for video {VIDEO_ID}...")
        
        cur.execute("""
            UPDATE projects 
            SET thumbnail_url = %s 
            WHERE source_video_url LIKE %s
            RETURNING id, title
        """, (THUMBNAIL_URL, f"%{VIDEO_ID}%"))
        
        updated = cur.fetchall()
        
        if updated:
            for row in updated:
                print(f"✅ Updated Project: {row[0]} ({row[1]})")
            conn.commit()
        else:
            print("❌ No project found to update.")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_thumbnail()
