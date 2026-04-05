import psycopg2, os
from dotenv import load_dotenv
load_dotenv('app/.env')
try:
    conn=psycopg2.connect(host='127.0.0.1', user='n8n', password='n8n', dbname='antigravity')
    cur=conn.cursor()
    cur.execute('SELECT id, project_status, source_video_url, created_at FROM projects ORDER BY created_at DESC LIMIT 10')
    rows = cur.fetchall()
    print('DATABASE CHECK:')
    for r in rows: print(r)
except Exception as e:
    print(f'DB Error: {e}')
