import psycopg2, os
from dotenv import load_dotenv
load_dotenv('app/.env')
try:
    conn=psycopg2.connect(os.getenv('DATABASE_URL'))
    cur=conn.cursor()
    cur.execute("SELECT current_database(), current_user")
    print(f'DB Info: {cur.fetchone()}')
    cur.execute("SELECT id, created_at FROM projects ORDER BY created_at DESC LIMIT 5")
    rows = cur.fetchall()
    print('Recent projects:')
    for r in rows: print(r)
except Exception as e:
    print(f'Error: {e}')
