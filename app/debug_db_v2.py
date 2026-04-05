import psycopg2, os
from dotenv import load_dotenv
load_dotenv('app/.env')
try:
    conn=psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB','antigravity'), 
        user=os.getenv('POSTGRES_USER','n8n'), 
        password=os.getenv('POSTGRES_PASSWORD','n8n'), 
        host='127.0.0.1'
    )
    cur=conn.cursor()
    cur.execute("SELECT id, created_at FROM projects ORDER BY created_at DESC LIMIT 5")
    rows = cur.fetchall()
    print('Recent projects:')
    for r in rows: print(r)
except Exception as e:
    print(f'Error: {e}')
