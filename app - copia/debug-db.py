import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    "user": "n8n",
    "password": "n8n",
    "host": "localhost",
    "port": 5432,
    "database": "antigravity"
}

def run():
    projectId = 'ad355c8b-e0d4-444e-3bb7-64b5648bd0c99'
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        query = 'UPDATE "projects" SET "status" = %s::job_status, "progress" = %s WHERE "id" = %s'
        params = ('PROCESSING', 20, projectId)
        
        full_query = cur.mogrify(query, params).decode('utf-8')
        print(f"DEBUG SQL: {full_query}")
        
        cur.execute(query, params)
        conn.commit()
        print("UPDATE SUCCESSFUL")
        
    except Exception as e:
        print(f"UPDATE FAILED: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    run()
