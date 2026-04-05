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
    
    # Get user ID
    cursor.execute("SELECT id, email FROM users WHERE email LIKE '%jpimasreiser%'")
    user = cursor.fetchone()
    
    if not user:
        print("❌ Usuario no encontrado")
        sys.exit(1)
    
    user_id = user[0]
    user_email = user[1]
    
    print(f"✅ Usuario: {user_email}")
    print(f"   ID: {user_id}\n")
    
    # Get all project IDs from clips
    cursor.execute("""
        SELECT DISTINCT c.project_id
        FROM clips c
        LEFT JOIN projects p ON c.project_id = p.id
        WHERE p.user_id IS NULL OR p.user_id != %s
    """, (user_id,))
    
    projects_to_fix = cursor.fetchall()
    
    if not projects_to_fix:
        print("✅ Todos los proyectos ya están correctamente asignados")
    else:
        print(f"⚙️  Actualizando {len(projects_to_fix)} proyectos...\n")
        
        for project_row in projects_to_fix:
            project_id = project_row[0]
            
            if project_id is None:
                continue
                
            cursor.execute("""
                UPDATE projects 
                SET user_id = %s 
                WHERE id = %s
            """, (user_id, project_id))
            
            print(f"✅ Proyecto {str(project_id)[:8]}... actualizado")
        
        conn.commit()
        print(f"\n✅ ¡{len(projects_to_fix)} proyectos actualizados correctamente!")
        
        # Verify
        cursor.execute("""
            SELECT COUNT(*) 
            FROM clips c
            JOIN projects p ON c.project_id = p.id
            WHERE p.user_id = %s
        """, (user_id,))
        
        valid_count = cursor.fetchone()[0]
        print(f"\n🎉 Ahora tienes {valid_count} clips accesibles")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
