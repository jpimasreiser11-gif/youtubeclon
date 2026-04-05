import psycopg2
import sys

def add_render_columns():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="antigravity",
            user="n8n",
            password="n8n"
        )
        cur = conn.cursor()
        
        # Add columns if they don't exist
        cur.execute("""
            ALTER TABLE clips 
            ADD COLUMN IF NOT EXISTS render_status TEXT DEFAULT 'idle',
            ADD COLUMN IF NOT EXISTS render_progress INTEGER DEFAULT 0,
            ADD COLUMN IF NOT EXISTS render_error TEXT
        """)
        
        conn.commit()
        print("✅ Success: Added rendering columns to 'clips' table.")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    add_render_columns()
