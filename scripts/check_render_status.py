import psycopg2
import sys

def check_db():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="antigravity",
            user="n8n",
            password="n8n"
        )
        cur = conn.cursor()
        
        # Check columns
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'clips' AND column_name IN ('render_status', 'render_progress', 'render_error')")
        cols = [r[0] for r in cur.fetchall()]
        print(f"Found columns: {cols}\n")
        
        # Check rows
        cur.execute("SELECT id, render_status, render_progress, render_error FROM clips WHERE render_status != 'idle' OR render_progress > 0")
        rows = cur.fetchall()
        print(f"Found {len(rows)} clips in progress/completed/failed state:")
        for r in rows:
            print(f"ID: {r[0]} | Status: {r[1]} | Progress: {r[2]}% | Error: {r[3]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
