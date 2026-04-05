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
    
    print(f"✅ Usuario encontrado: {user_email}")
    print(f"   ID: {user_id}\n")
    
    # Get ALL clips and check their associations
    cursor.execute("""
        SELECT 
            c.id,
            c.project_id,
            p.id as project_check,
            p.user_id,
            c.transcription_status
        FROM clips c
        LEFT JOIN projects p ON c.project_id = p.id
        ORDER BY c.created_at DESC
        LIMIT 20
    """)
    
    clips = cursor.fetchall()
    
    print(f"=== ANÁLISIS DE CLIPS ===\n")
    
    valid_clips = []
    broken_clips = []
    
    for clip in clips:
        clip_id = clip[0]
        project_id = clip[1]
        project_check = clip[2]
        project_user_id = clip[3]
        status = clip[4]
        
        if project_check is None:
            print(f"❌ Clip {clip_id[:8]}...")
            print(f"   Project ID: {project_id} NO EXISTE")
            broken_clips.append(clip_id)
        elif project_user_id != user_id:
            print(f"⚠️  Clip {clip_id[:8]}...")
            print(f"   Project pertenece a otro usuario: {project_user_id}")
            broken_clips.append(clip_id)
        else:
            print(f"✅ Clip {clip_id[:8]}...")
            print(f"   Asociado correctamente")
            print(f"   Status: {status}")
            valid_clips.append(clip_id)
        
        print()
    
    print("\n" + "="*70)
    print(f"\nRESUMEN:")
    print(f"- Clips válidos: {len(valid_clips)}")
    print(f"- Clips con problemas: {len(broken_clips)}")
    
    if broken_clips and valid_clips:
        print(f"\n⚠️  Hay {len(broken_clips)} clips con problemas de asociación")
        print(f"\n¿Quieres que los arregle? (Los asociaré al usuario {user_email})")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
