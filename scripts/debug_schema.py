import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../app/.env'))

db_config = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': 'antigravity',
    'user': os.getenv('POSTGRES_USER', 'n8n'),
    'password': os.getenv('POSTGRES_PASSWORD', 'n8n')
}

print(f"🔌 Connecting to {db_config['database']} as {db_config['user']}...")

try:
    conn = psycopg2.connect(**db_config)
    conn.autocommit = True
    cur = conn.cursor()
    
    # 1. Check current columns
    print("📊 Existing columns in 'clips':")
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'clips'")
    rows = cur.fetchall()
    cols = [r[0] for r in rows]
    for c in cols:
        print(f" - {c}")
        
    if 'transcript_json' in cols:
        print("✅ 'transcript_json' column FOUND.")
    else:
        print("❌ 'transcript_json' column MISSING. Attempting to add...")
        try:
            cur.execute("ALTER TABLE clips ADD COLUMN transcript_json JSONB")
            print("✅ Column added successfully.")
        except Exception as e:
            print(f"⚠️ Error adding column: {e}")

    # 2. Try update
    print("📝 Testing UPDATE on 'transcript_json'...")
    clip_id = "24d43931-ffed-4911-a2a3-0455c71901c8"
    try:
        cur.execute("UPDATE clips SET transcript_json = '[]'::jsonb WHERE id = %s", (clip_id,))
        print("✅ UPDATE successful.")
    except Exception as e:
        print(f"❌ UPDATE failed: {e}")

    cur.close()
    conn.close()

except Exception as e:
    print(f"💥 Critical DB Error: {e}")
