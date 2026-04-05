import psycopg2, os
from dotenv import load_dotenv
load_dotenv('app/.env')
conn=psycopg2.connect(dbname=os.getenv('POSTGRES_DB','antigravity'), user=os.getenv('POSTGRES_USER','n8n'), password=os.getenv('POSTGRES_PASSWORD','n8n'), host='127.0.0.1')
cur=conn.cursor()
cur.execute('SELECT count(*) FROM projects')
print(f"Total projects: {cur.fetchone()[0]}")
cur.execute('SELECT id, created_at FROM projects ORDER BY created_at DESC LIMIT 3')
for r in cur.fetchall(): print(r)
