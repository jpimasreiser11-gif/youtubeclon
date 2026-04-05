import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../app/.env'))

# Explicitly target 'antigravity' as per .env
db_config = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': 'antigravity',
    'user': os.getenv('POSTGRES_USER', 'n8n'),
    'password': os.getenv('POSTGRES_PASSWORD', 'n8n')
}

print(f"Connecting to database: {db_config['database']}")

try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()

    # 1. Create transcriptions table
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS transcriptions (
        id SERIAL PRIMARY KEY,
        clip_id UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
        language VARCHAR(10),
        words JSONB,
        edited BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT unique_clip_transcription UNIQUE (clip_id)
    );
    """
    cur.execute(create_table_sql)
    print("✅ Table 'transcriptions' checked/created.")

    # 2. Add transcript_json column to clips
    alter_table_sql = """
    ALTER TABLE clips 
    ADD COLUMN transcript_json JSONB;
    """
    try:
        cur.execute(alter_table_sql)
        print("✅ Column 'transcript_json' added to 'clips'.")
    except psycopg2.errors.DuplicateColumn:
        print("⚠️ Column 'transcript_json' already exists (DuplicateColumn error).")
        conn.rollback() 
        cur = conn.cursor() # Get new cursor after rollback
    except Exception as e:
        print(f"⚠️ Error adding column (might exist): {e}")
        conn.rollback()
        cur = conn.cursor()

    conn.commit()
    
    # 3. VERIFY COLUMNS
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'clips'
    """)
    rows = cur.fetchall()
    print("📋 Current columns in 'clips':")
    for r in rows:
        print(f" - {r[0]}")

    cur.close()
    conn.close()
    print("🚀 Migration completed successfully for 'antigravity' DB.")

except Exception as e:
    print(f"❌ Error during migration: {e}")
