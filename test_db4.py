import psycopg2, os
from dotenv import load_dotenv
load_dotenv('app/.env')
conn=psycopg2.connect(dbname=os.getenv('POSTGRES_DB','antigravity'), user=os.getenv('POSTGRES_USER','n8n'), password=os.getenv('POSTGRES_PASSWORD','n8n'), host='127.0.0.1')
cur=conn.cursor()
cur.execute("SELECT progress_percent, eta_seconds, current_step FROM projects WHERE id = 'e8dcfa6c-c6ae-439b-ab48-b3f80dee91d7'")
print(cur.fetchone())
