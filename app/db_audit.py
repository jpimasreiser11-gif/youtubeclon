import psycopg2, os
from dotenv import load_dotenv
load_dotenv('app/.env')
try:
    conn=psycopg2.connect(host='127.0.0.1', user='n8n', password='n8n', dbname='antigravity')
    cur=conn.cursor()
    cur.execute('SELECT COUNT(*) FROM projects')
    print(f'Projects count: {cur.fetchone()[0]}')
    cur.execute('SELECT * FROM projects ORDER BY created_at DESC LIMIT 5')
    for r in cur.fetchall(): print(r)
except Exception as e:
    print(f'DB Error: {e}')
