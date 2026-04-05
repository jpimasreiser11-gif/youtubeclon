import psycopg2
import json

db_config = {
    'dbname': 'antigravity',
    'user': 'n8n',
    'password': 'n8n',
    'host': 'localhost'
}

try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    
    # List tables
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = [t[0] for t in cur.fetchall()]
    print("Tables available:", tables)
    
    if 'scheduled_publications' in tables:
        print("\n--- scheduled_publications ---")
        cur.execute("SELECT * FROM scheduled_publications ORDER BY created_at DESC LIMIT 5")
        rows = cur.fetchall()
        for row in rows:
            print(row)
            
    if 'scheduled_uploads' in tables:
        print("\n--- scheduled_uploads ---")
        cur.execute("SELECT * FROM scheduled_uploads ORDER BY created_at DESC LIMIT 5") # Assuming created_at exists, else remove ORDER
        rows = cur.fetchall()
        for row in rows:
            print(row)
            
    if 'upload_history' in tables:
        print("\n--- upload_history ---")
        cur.execute("SELECT * FROM upload_history ORDER BY created_at DESC LIMIT 5")
        rows = cur.fetchall()
        for row in rows:
            print(row)

    cur.close()
    conn.close()

except Exception as e:
    print("Error:", e)
