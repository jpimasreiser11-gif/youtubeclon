import psycopg2
import json
import os
from pathlib import Path
from dotenv import load_dotenv

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

target_ids = [
    'b5360c0f-a190-4d10-85f8-79ae3222384c',
    '821a3ee0-684c-41ac-8266-9e1e17df20fc',
    '57a0845e-e4c0-4eb5-be40-9bfa9a00ec1f'
]

try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    # Query specific interesting IDs
    cur.execute("SELECT id, render_status, render_progress, render_error FROM clips WHERE id::text IN %s", (tuple(target_ids),))
    rows = cur.fetchall()
    
    columns = [desc[0] for desc in cur.description]
    print(json.dumps([dict(zip(columns, r)) for r in rows], indent=2, default=str))
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
