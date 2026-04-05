import psycopg2
import os
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../app/.env'))

db_config = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'edumind_viral'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'n8n')
}

try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    rows = cur.fetchall()
    print("Tables in database:")
    for r in rows:
        print(r[0])
    
    # Check if transcriptions exist
    if ('transcriptions',) not in rows:
        print("WARNING: 'transcriptions' table MISSING!")
    else:
        cur.execute("SELECT clip_id FROM transcriptions LIMIT 5")
        rows = cur.fetchall()
        print("Found transcriptions for clips:")
        for r in rows:
            print(r[0])
    conn.close()
except Exception as e:
    print(e)
