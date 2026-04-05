import psycopg2
import os
import sys
from dotenv import load_dotenv

if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


load_dotenv('.env')

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    dbname=os.getenv('POSTGRES_DB', 'antigravity'),
    user=os.getenv('POSTGRES_USER', 'n8n'),
    password=os.getenv('POSTGRES_PASSWORD', 'n8n')
)
cur = conn.cursor()
cur.execute('SELECT id, project_status, current_step, progress_percent, updated_at FROM projects ORDER BY updated_at DESC')
rows = cur.fetchall()
for row in rows:
    print(row)
cur.close()
conn.close()
