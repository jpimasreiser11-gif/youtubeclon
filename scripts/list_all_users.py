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
    
    # Get ALL users
    cursor.execute("SELECT id, email FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    
    print("\n=== TODOS LOS USUARIOS EN LA BASE DE DATOS ===\n")
    for i, user in enumerate(users, 1):
        print(f"{i}. Email: {user[1]}")
        print(f"   ID: {user[0]}")
        
        # Count their projects
        cursor.execute("SELECT COUNT(*) FROM projects WHERE user_id = %s", (user[0],))
        project_count = cursor.fetchone()[0]
        print(f"   Proyectos: {project_count}")
        print()
    
    print("="*70)
    print(f"\nTotal usuarios: {len(users)}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
