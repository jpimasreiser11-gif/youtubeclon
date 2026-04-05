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
    
    # Get all clips with user and project info
    cursor.execute("""
        SELECT 
            c.id as clip_id,
            c.project_id,
            c.transcription_status,
            p.id as project_id_check,
            u.email as user_email,
            p.status as project_status
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
            print(f"   Project ID: {row[1]} (Status: {row[5] or 'N/A'})")
            print(f"   User: {row[4] or 'NO USER ASSOCIATED'}")
            print(f"   Transcription: {row[2] or 'pending'}")
            print("-" * 70)
    else:
        print("❌ No hay clips en la base de datos")
    
    # Also check users
    cursor.execute("SELECT id, email FROM users LIMIT 5")
    users = cursor.fetchall()
    
    print("\n=== USUARIOS EN LA BASE DE DATOS ===\n")
    if users:
        for user in users:
            print(f"- {user[1]}")
            print(f"  ID: {user[0]}")
    else:
        print("❌ No hay usuarios en la base de datos")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
