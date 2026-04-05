import psycopg2
import json
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path('app/.env')
load_dotenv(dotenv_path=env_path)

db_config = {
    'host': os.getenv('POSTGRES_HOST', '127.0.0.1'),
    'database': os.getenv('POSTGRES_DB', 'antigravity'),
    'user': os.getenv('POSTGRES_USER', 'n8n'),
    'password': os.getenv('POSTGRES_PASSWORD', 'n8n'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    # Query all clips in 'processing' status or with progress
    cur.execute("SELECT id, render_status, render_progress, render_error FROM clips WHERE render_status = 'processing' OR render_progress > 0")
    rows = cur.fetchall()
    
    if rows:
        columns = [desc[0] for desc in cur.description]
        print(f"\n--- FOUND {len(rows)} ACTIVE/STUCK JOBS ---")
        for row in rows:
            result = dict(zip(columns, row))
            print(json.dumps(result, indent=2, default=str))
    else:
        print("\n✅ No active or stuck rendering jobs found.")
        
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
