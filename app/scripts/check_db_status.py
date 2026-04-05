import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "user": "n8n",
    "password": "n8n",
    "host": "localhost",
    "port": 5432,
    "database": "antigravity"
}

def check_latest_job():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("--- Latest 5 Projects ---")
        cur.execute("SELECT id, project_status, created_at FROM projects ORDER BY created_at DESC LIMIT 5")
        rows = cur.fetchall()
        for row in rows:
            print(f"ID: {row[0]} | Status: {row[1]} | Created: {row[2]}")
            
            # Check clips count for this project
            cur.execute("SELECT count(*) FROM clips WHERE project_id = %s", (row[0],))
            clip_count = cur.fetchone()[0]
            print(f"   -> Clips generated: {clip_count}")

            # Check if there are any error columns if schema has them (assuming standard schema for now)
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    check_latest_job()
