import psycopg2, os
from dotenv import load_dotenv

load_dotenv('app/.env')
conn = psycopg2.connect(
    dbname=os.getenv('POSTGRES_DB','antigravity'), 
    user=os.getenv('POSTGRES_USER','n8n'), 
    password=os.getenv('POSTGRES_PASSWORD','n8n'), 
    host='127.0.0.1'
)
cur = conn.cursor()
cur.execute("SELECT id, project_status, progress_percent, eta_seconds, current_step FROM projects WHERE id = 'e8dcfa6c-c6ae-439b-ab48-b3f80dee91d7'")
print("Active project row:", cur.fetchone())

cur.execute("SELECT id, project_status, progress_percent, eta_seconds, created_at FROM projects ORDER BY created_at DESC LIMIT 3")
print("Top 3 projects:")
for row in cur.fetchall():
    print(row)
