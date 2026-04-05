import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="localhost",
        database="antigravity",
        user="n8n",
        password="n8n"
    )
    cursor = conn.cursor()
    
    # Get all clips with simple join
    cursor.execute("""
        SELECT 
            c.id,
            c.project_id,
            c.transcription_status,
            u.email
        FROM clips c
        LEFT JOIN projects p ON c.project_id = p.id
        LEFT JOIN users u ON p.user_id = u.id
        ORDER BY c.created_at DESC
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    
    print("\n=== CLIPS EN LA BASE DE DATOS ===\n")
    if rows:
        for i, row in enumerate(rows, 1):
            print(f"{i}. Clip ID: {row[0]}")
            print(f"   Project ID: {row[1]}")
            print(f"   User Email: {row[3] or 'NO USER'}")
            print(f"   Transcription Status: {row[2] or 'pending'}")
            print("-" * 70)
    else:
        print("❌ No hay clips")
    
    # Check users
    cursor.execute("SELECT id, email FROM users LIMIT 5")
    users = cursor.fetchall()
    
    print("\n=== USUARIOS ===\n")
    if users:
        for user in users:
            print(f"- Email: {user[1]}")
            print(f"  ID: {user[0]}\n")
    else:
        print("❌ No hay usuarios")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
