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
    
    # Get all clips with their project info
    cursor.execute("""
        SELECT c.id, c.project_id, p.user_id, c.transcription_status 
        FROM clips c 
        LEFT JOIN projects p ON c.project_id = p.id
        ORDER BY c.created_at DESC 
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    
    print("\n=== CLIPS EN BASE DE DATOS ===\n")
    if rows:
        for row in rows:
            print(f"Clip ID: {row[0]}")
            print(f"Project ID: {row[1]}")
            print(f"User ID: {row[2]}")
            print(f"Status: {row[3]}")
            print("-" * 50)
    else:
        print("No se encontraron clips en la base de datos.")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
