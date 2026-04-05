import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../app/.env'))

db_config = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': 'antigravity',
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'n8n')
}

try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute("SELECT id FROM clips ORDER BY created_at DESC LIMIT 5")
    rows = cur.fetchall()
    print("Recent Clips IDs in DB:")
    for r in rows:
        print(f"{r[0]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
