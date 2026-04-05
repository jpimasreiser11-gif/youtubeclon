import psycopg2
import os

try:
    host = os.environ.get('POSTGRES_HOST', '127.0.0.1')
    dbname = os.environ.get('POSTGRES_DB', 'antigravity')
    user = os.environ.get('POSTGRES_USER', 'n8n')
    password = os.environ.get('POSTGRES_PASSWORD', 'n8n')

    conn = psycopg2.connect(host=host, dbname=dbname, user=user, password=password)
    c = conn.cursor()
    
    with open('migrations/003_automation_schema.sql', 'r') as f:
        sql = f.read()
    
    c.execute(sql)
    conn.commit()
    print("Migration applied successfully!")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
