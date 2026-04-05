import psycopg2, os
from dotenv import load_dotenv
load_dotenv('app/.env')
conn=psycopg2.connect(dbname=os.getenv('POSTGRES_DB','antigravity'), user=os.getenv('POSTGRES_USER','n8n'), password=os.getenv('POSTGRES_PASSWORD','n8n'), host='127.0.0.1')
cur=conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
for r in cur.fetchall(): print(r)
cur.execute("SELECT count(*) FROM projects")
print(f'Total projects in DB: {cur.fetchone()[0]}')
