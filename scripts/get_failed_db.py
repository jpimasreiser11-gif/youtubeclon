import psycopg2
import os
from datetime import datetime

try:
    conn = psycopg2.connect(
        dbname=os.getenv('POSTGRES_DB','antigravity'), 
        user=os.getenv('POSTGRES_USER','n8n'), 
        password=os.getenv('POSTGRES_PASSWORD','n8n'), 
        host='127.0.0.1'
    )
    cur = conn.cursor()
    cur.execute("SELECT id, project_status, current_step, error_message, created_at FROM projects WHERE project_status = 'FAILED' ORDER BY created_at DESC LIMIT 5")
    rows = cur.fetchall()
    
    if not rows:
        print("No FAILED projects found.")
    else:
        print(f"Found {len(rows)} FAILED projects:")
        for r in rows:
            print(f"ID: {r[0]} | Status: {r[1]} | Step: {r[2]}")
            print(f"Error: {r[3]}")
            print("-" * 50)
            
except Exception as e:
    print(f"DB Error: {e}")
