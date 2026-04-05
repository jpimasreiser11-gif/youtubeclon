import psycopg2, os
from dotenv import load_dotenv
load_dotenv('app/.env')
conn=psycopg2.connect(dbname=os.getenv('POSTGRES_DB','antigravity'), user=os.getenv('POSTGRES_USER','n8n'), password=os.getenv('POSTGRES_PASSWORD','n8n'), host='127.0.0.1')
cur=conn.cursor()
cur.execute("SELECT id, project_status, created_at FROM projects WHERE created_at > (NOW() - INTERVAL '1 day') ORDER BY created_at DESC")
rows = cur.fetchall()
print(f'Count: {len(rows)}')
for row in rows:
    print(row)
