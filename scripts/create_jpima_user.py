import psycopg2
import sys
import uuid

try:
    conn = psycopg2.connect(
        host="localhost",
        database="antigravity",
        user="n8n",
        password="n8n"
    )
    cursor = conn.cursor()
    
    target_email = "j.pima@example.com"
    
    print(f"🔧 Creando usuario: {target_email}\n")
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE email = %s", (target_email,))
    user = cursor.fetchone()
    
    if user:
        user_id = user[0]
        print(f"✅ Usuario ya existe con ID: {user_id}")
    else:
        # Create new user
        user_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO users (id, email) 
            VALUES (%s, %s)
        """, (user_id, target_email))
        conn.commit()
        print(f"✅ Usuario creado con ID: {user_id}")
    
    print(f"\n⚙️  Asignando TODOS los proyectos a {target_email}...\n")
    
    # Update ALL projects to this user
    cursor.execute("UPDATE projects SET user_id = %s", (user_id,))
    updated_count = cursor.rowcount
    conn.commit()
    
    print(f"✅ {updated_count} proyectos asignados correctamente!")
    
    # Verify
    cursor.execute("""
        SELECT COUNT(*) 
        FROM clips c
        JOIN projects p ON c.project_id = p.id
        WHERE p.user_id = %s
    """, (user_id,))
    
    clip_count = cursor.fetchone()[0]
    
    print(f"\n🎉 ÉXITO!")
    print(f"   Usuario: {target_email}")
    print(f"   Proyectos: {updated_count}")
    print(f"   Clips accesibles: {clip_count}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
