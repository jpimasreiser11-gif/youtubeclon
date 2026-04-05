import psycopg2
import sys

def get_columns():
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="antigravity",
            user="n8n",
            password="n8n"
        )
        cur = conn.cursor()
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'clips'")
        cols = cur.fetchall()
        print("Columns for 'clips':")
        for c in cols:
            print(f"  {c[0]}: {c[1]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_columns()
