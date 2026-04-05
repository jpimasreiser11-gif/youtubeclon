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
    
    # Check if the specific clip exists
    clip_id = "24d43931-ffed-4911-a2a3-0455c71901c8"
    cursor.execute("SELECT id, project_id FROM clips WHERE id = %s", (clip_id,))
    result = cursor.fetchone()
    
    if result:
        print(f"✅ Clip {clip_id} EXISTS")
        print(f"   Project ID: {result[1]}")
    else:
        print(f"❌ Clip {clip_id} DOES NOT EXIST")
        print("\n=== Creating clip entry ===")
        
        # Get or create a project
        project_id = "4358ba66-9f4a-4a10-aeac-363372ecfc3ef"
        
        # Check if project exists, if not create it
        cursor.execute("SELECT id FROM projects WHERE id = %s", (project_id,))
        if not cursor.fetchone():
            print(f"Creating project {project_id}...")
            # Need a user_id - let's get the first user or create one
            cursor.execute("SELECT id FROM users LIMIT 1")
            user_result = cursor.fetchone()
            if user_result:
                user_id = user_result[0]
            else:
                print("No users found - creating test user...")
                user_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO users (id, email, name) 
                    VALUES (%s, 'test@example.com', 'Test User')
                """, (user_id,))
            
            cursor.execute("""
                INSERT INTO projects (id, user_id, name, status) 
                VALUES (%s, %s, 'Test Project', 'completed')
            """, (project_id, user_id))
            print(f"✅ Project created")
        
        # Create the clip
        print(f"Creating clip {clip_id}...")
        cursor.execute("""
            INSERT INTO clips (id, project_id, start_time, end_time, transcription_status) 
            VALUES (%s, %s, 0, 19.06, 'completed')
        """, (clip_id, project_id))
        
        conn.commit()
        print(f"✅ Clip created successfully!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
