import psycopg2, os
from dotenv import load_dotenv
load_dotenv('app/.env')
conn=psycopg2.connect(dbname=os.getenv('POSTGRES_DB','antigravity'), user=os.getenv('POSTGRES_USER','n8n'), password=os.getenv('POSTGRES_PASSWORD','n8n'), host='127.0.0.1')
cur=conn.cursor()
cur.execute("SELECT id, project_status, progress_percent, current_step, updated_at FROM projects WHERE id = '430192c1-36bf-41b4-a11c-22a42314e3a1'")
print("Job 430192c1:", cur.fetchone())
cur.execute("SELECT id, project_status, created_at FROM projects ORDER BY created_at DESC LIMIT 5")
print("Latest 5 projects:")
for r in cur.fetchall(): print(r)
