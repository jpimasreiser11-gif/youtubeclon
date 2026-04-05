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
    
    clip_id = "44c605f9-882e-4bc8-b82a-9a101299b452"
    
    # Check if this clip exists
    cursor.execute("""
        SELECT c.id, c.project_id, p.user_id, p.id as project_check
        FROM clips c
        LEFT JOIN projects p ON c.project_id = p.id
        WHERE c.id = %s
    """, (clip_id,))
    
    result = cursor.fetchone()
    
    if result:
        print(f"✅ Clip {clip_id} EXISTE")
        print(f"   Project ID: {result[1]}")
        print(f"   Project exists: {'✅' if result[3] else '❌'}")
        print(f"   User ID: {result[2]}")
    else:
        print(f"❌ Clip {clip_id} NO EXISTE en la base de datos")
        print("\nEste clip se muestra en la UI pero no está en la DB.")
        print("La UI probablemente está cargando clips desde un archivo JSON o caché.")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
