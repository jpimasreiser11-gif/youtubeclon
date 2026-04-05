import psycopg2
import sys

def get_schema():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="antigravity",
            user="n8n",
            password="n8n"
        )
        cur = conn.cursor()
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'transcriptions'")
        cols = cur.fetchall()
        print("Schema for 'transcriptions':")
        for c in cols:
            print(f"  {c[0]}: {c[1]}")
            
        cur.execute("SELECT clip_id FROM transcriptions LIMIT 1")
        row = cur.fetchone()
        if row:
            print(f"Sample clip_id from transcriptions: '{row[0]}' (type: {type(row[0])})")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_schema()
