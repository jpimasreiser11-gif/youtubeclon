import psycopg2
import json

db_config = {
    'dbname': 'antigravity',
    'user': 'n8n',
    'password': 'n8n',
    'host': 'localhost'
}

def fix_schema():
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Check platform_connections columns
        print("Checking platform_connections columns...")
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'platform_connections'")
        columns = [row[0] for row in cur.fetchall()]
        print("Platform Connections Columns:", columns)
        
        # Check platform_credentials columns
        print("Checking platform_credentials columns...")
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'platform_credentials'")
        columns = [row[0] for row in cur.fetchall()]
        print("Platform Credentials Columns:", columns)

        # Create scheduled_publications if missing
        print("\nCreating scheduled_publications table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_publications (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                clip_id UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
                platform VARCHAR(50) NOT NULL,
                scheduled_at TIMESTAMPTZ NOT NULL,
                status VARCHAR(20) DEFAULT 'pending', -- pending, processing, published, failed, uploading, success
                title TEXT,
                description TEXT,
                tags TEXT,
                privacy VARCHAR(20) DEFAULT 'private',
                video_url TEXT,
                error_message TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                completed_at TIMESTAMPTZ,
                started_at TIMESTAMPTZ
            );
        """)
        # Ensure status column allows 'uploading' and 'success' (it is varchar so it's fine)
        
        conn.commit()
        
        # Verify creation
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'scheduled_publications'")
        if cur.fetchone():
            print("✅ scheduled_publications table exists/created.")
        else:
            print("❌ Failed to create scheduled_publications table.")

        cur.close()
        conn.close()
        
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    fix_schema()
