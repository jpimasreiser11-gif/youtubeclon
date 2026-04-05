import psycopg2

# Configuration
DB_HOST = "127.0.0.1"
DB_NAME = "antigravity"
DB_USER = "n8n"
DB_PASS = "n8n"
DB_PORT = "5432"

TARGET_ID = "9ce814df-9c1e-4de0-b92e-84c819b9fa00"

def check_users():
    print(f"🔌 Connecting to database...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT
        )
        cur = conn.cursor()
        
        cur.execute("SELECT id, email, name FROM users")
        users = cur.fetchall()
        
        print("\n👥 Users in DB:")
        for u in users:
            email = u[1]
            if "jpima" in email:
                print(f"FOUND TARGET: {email}")
                print(f"FULL ID: {u[0]}")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_users()
