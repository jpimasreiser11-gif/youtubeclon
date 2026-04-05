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
    
    # Find the user with "test@example.com"
    cursor.execute("SELECT id, email FROM users WHERE email = 'test@example.com'")
    original_user = cursor.fetchone()
    
    if not original_user:
        print("❌ Usuario test@example.com no encontrado")
        print("\nUsuarios disponibles:")
        cursor.execute("SELECT id, email FROM users")
        for u in cursor.fetchall():
            print(f"  - {u[1]} ({u[0]})")
        sys.exit(1)
    
    original_user_id = original_user[0]
    original_email = original_user[1]
    
    print(f"🔄 Restaurando proyectos a: {original_email}")
    print(f"   ID: {original_user_id}\n")
    
    # Get all projects
    cursor.execute("SELECT id FROM projects")
    projects = cursor.fetchall()
    
    print(f"⚙️  Actualizando {len(projects)} proyectos...\n")
    
    # Update all projects to original user
    cursor.execute("""
        UPDATE projects 
        SET user_id = %s
    """, (original_user_id,))
    
    conn.commit()
    
    print(f"✅ ¡{len(projects)} proyectos restaurados correctamente!")
    print(f"\n📋 Todos los proyectos ahora pertenecen a: {original_email}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
