import psycopg2
from dotenv import load_dotenv
import os
import json

load_dotenv()

DB_CONFIG = {
    "user": "n8n",
    "password": "n8n",
    "host": "localhost",
    "port": 5432,
    "database": "antigravity"
}

def run():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'projects' ORDER BY column_name")
        cols = cur.fetchall()
        print("COLS:" + json.dumps(cols))
            
        cur.execute("SELECT enumlabel FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'job_status' ORDER BY enumlabel")
        enums = cur.fetchall()
        print("ENUMS:" + json.dumps([e[0] for e in enums]))
            
    except Exception as e:
        print(f"INSPECTION FAILED: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run()
