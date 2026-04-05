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
    
    # Get test@example.com user
    cursor.execute("SELECT id FROM users WHERE email = 'test@example.com'")
    user = cursor.fetchone()
    
    if not user:
        print("❌ Usuario test@example.com no encontrado")
        sys.exit(1)
    
    user_id = user[0]
    print(f"Usuario: test@example.com")
    print(f"ID: {user_id}\n")
    
    # Get clips that SHOULD be accessible
    cursor.execute("""
        SELECT 
            c.id as clip_id,
            c.project_id,
            p.id as project_check,
            p.user_id as project_user
        FROM clips c
        LEFT JOIN projects p ON c.project_id = p.id
        WHERE p.user_id = %s
        ORDER BY c.created_at DESC
        LIMIT 10
    """, (user_id,))
    
    clips = cursor.fetchall()
    
    print(f"=== CLIPS ACCESIBLES PARA test@example.com ===\n")
    if clips:
        for i, clip in enumerate(clips, 1):
            print(f"{i}. Clip ID: {clip[0]}")
            print(f"   Project ID: {clip[1]}")
            print(f"   Project exists: {'✅' if clip[2] else '❌'}")
            print(f"   Project user matches: {'✅' if clip[3] == user_id else '❌'}")
            print()
    else:
        print("❌ No hay clips accesibles para este usuario")
        print("\nVerificando clips sin proyecto asignado...")
        
        cursor.execute("""
            SELECT c.id, c.project_id
            FROM clips c
            LEFT JOIN projects p ON c.project_id = p.id
            WHERE p.id IS NULL
            LIMIT 5
        """)
        
        orphan_clips = cursor.fetchall()
        if orphan_clips:
            print(f"\n⚠️  Hay {len(orphan_clips)} clips 'huérfanos' (sin proyecto asociado):")
            for clip in orphan_clips:
                print(f"   - Clip {clip[0]} → Project {clip[1]} (no existe)")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
