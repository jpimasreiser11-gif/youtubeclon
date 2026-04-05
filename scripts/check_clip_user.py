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
    
    # Get project info from clip
    cursor.execute("""
        SELECT c.id, c.project_id, p.user_id, p.id
        FROM clips c
        LEFT JOIN projects p ON c.project_id = p.id
        WHERE c.id = %s::uuid
    """, (clip_id,))
    
    result = cursor.fetchone()
    
    if result:
        print(f"Clip ID: {result[0]}")
        print(f"Project ID from clip: {result[1]}")
        print(f"Project user_id: {result[2]}")
        print(f"Project ID from join: {result[3]}")
        
        if result[2] is None:
            print("\n⚠️  Project has no user_id, updating...")
            
            # Get first user
            cursor.execute("SELECT id FROM users LIMIT 1")
            user_row = cursor.fetchone()
            
            if user_row:
                user_id = user_row[0]
                print(f"Using user: {user_id}")
                
                cursor.execute(
                    "UPDATE projects SET user_id = %s WHERE id = %s::uuid",
                    (user_id, str(result[1]))
                )
                conn.commit()
                print("✅ Updated!")
            else:
                print("❌ No users found")
    else:
        print(f"❌ Clip {clip_id} not found")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
