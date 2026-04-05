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
    
    clip_id = "24d43931-ffed-4911-a2a3-0455c71901c8"
    project_id = "4358ba66-9f4a-4a10-aeac-363372ecfc3ef"
    
    # Get current project user_id
    cursor.execute("SELECT id, user_id FROM projects WHERE id = %s", (project_id,))
    project = cursor.fetchone()
    
    if project:
        print(f"✅ Project {project[0]} found")
        print(f"   Current user_id: {project[1]}")
        
        # Get a valid user from the users table
        cursor.execute("SELECT id, email FROM users LIMIT 1")
        user = cursor.fetchone()
        
        if user:
            print(f"\n✅ Found user: {user[1]} ({user[0]})")
            
            if project[1] != user[0]:
                print(f"\n⚠️  Updating project user_id to {user[0]}...")
                cursor.execute(
                    "UPDATE projects SET user_id = %s WHERE id = %s",
                    (user[0], project_id)
                )
                conn.commit()
                print("✅ Project user_id updated!")
            else:
                print("\n✅ Project already associated with correct user")
        else:
            print("\n❌ No users found in database")
            print("   Creating a test user...")
            cursor.execute("""
                INSERT INTO users (id, email, name)
                VALUES (gen_random_uuid(), 'admin@test.com', 'Admin User')
                RETURNING id, email
            """)
            new_user = cursor.fetchone()
            print(f"✅ Created user: {new_user[1]} ({new_user[0]})")
            
            cursor.execute(
                "UPDATE projects SET user_id = %s WHERE id = %s",
                (new_user[0], project_id)
            )
            conn.commit()
            print("✅ Project user_id updated!")
    else:
        print(f"❌ Project {project_id} not found")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
