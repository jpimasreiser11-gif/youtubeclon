import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "user": "n8n",
    "password": "n8n",
    "host": "localhost",
    "port": 5432,
    "database": "antigravity"
}

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'projects';
    """)
    cols = [r[0] for r in cur.fetchall()]
    print(f"Columns: {cols}")
    
    cur.execute("SELECT * FROM projects ORDER BY created_at DESC LIMIT 1;")
    row = cur.fetchone()
    
    if row:
        for i, col in enumerate(cols):
            print(f"{col}: {row[i]}")
            
    cur.close()
    conn.close()
except Exception as e:
    print(f"DB Error: {e}")
