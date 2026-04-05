import psycopg2, os
from dotenv import load_dotenv
load_dotenv('app/.env')
conn=psycopg2.connect(dbname=os.getenv('POSTGRES_DB','antigravity'), user=os.getenv('POSTGRES_USER','n8n'), password=os.getenv('POSTGRES_PASSWORD','n8n'), host='127.0.0.1')
cur=conn.cursor()
cur.execute('SELECT id, progress_percent, eta_seconds, current_step, created_at FROM projects ORDER BY created_at DESC LIMIT 5')
for row in cur.fetchall():
    print(f"{row[0]} | %: {row[1]} | ETA: {row[2]} | STEP: {row[3]} | DATE: {row[4]}")
