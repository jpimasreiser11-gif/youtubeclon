import os
import json
import sys
import psycopg2
from datetime import datetime, timedelta
import random

# FIX: Forzar UTF-8 en Windows para evitar UnicodeEncodeError con emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


# Database Configuration
DB_CONFIG = {
    'host': '127.0.0.1',
    'dbname': 'antigravity',
    'user': 'n8n',
    'password': 'n8n'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def orchestrate_daily_publications():
    print(f"[{datetime.now()}] [RUN] Starting Daily Automation Orchestrator...")
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Get enabled projects
        cur.execute("""
            SELECT id, title, publish_slots_per_day, publish_platforms 
            FROM projects 
            WHERE auto_publish_enabled = TRUE
        """)
        projects = cur.fetchall()
        
        if not projects:
            print("[SUCCESS] No projects marked for daily automation.")
            return

        print(f"[INFO] Found {len(projects)} projects for daily automation.")
        
        for project_id, project_title, slots, platforms in projects:
            print(f"\n[PROJECT] Processing Project: {project_title} (ID: {project_id})")
            
            # 2. Get top viral clips not yet scheduled (ordered by virality)
            cur.execute("""
                SELECT c.id, c.virality_score, c.title_generated, c.description_generated, c.project_id
                FROM clips c
                LEFT JOIN scheduled_publications sp ON c.id = sp.clip_id
                WHERE c.project_id = %s
                AND sp.id IS NULL
                AND (c.end_time - c.start_time) >= 45
                ORDER BY c.virality_score DESC, (c.end_time - c.start_time) DESC
                LIMIT %s
            """, (project_id, slots))
            
            top_clips = cur.fetchall()
            
            if not top_clips:
                print(f"   [WARN] No more unscheduled clips for this project.")
                continue
                
            print(f"   [INFO] Found {len(top_clips)} new viral clips to schedule.")
            
            # 3. Schedule clips for TODAY/TOMORROW
            now = datetime.now()
            base_times = [10, 15, 20] 
            
            for i, (clip_id, score, clip_title, clip_desc, pid) in enumerate(top_clips):
                hour = base_times[i % len(base_times)]
                
                scheduling_day = now.date()
                if now.hour >= hour:
                    scheduling_day += timedelta(days=1)
                
                scheduled_at = datetime.combine(scheduling_day, datetime.min.time()) + timedelta(hours=hour, minutes=random.randint(0, 59))
                
                # Split description and hashtags if they are stored in the same field
                desc_parts = clip_desc.split('\n\n')
                main_desc = desc_parts[0] if desc_parts else ""
                hashtags = desc_parts[1] if len(desc_parts) > 1 else ""

                for platform in platforms:
                    print(f"   [DATE] Scheduling: [{platform.upper()}] '{clip_title}' at {scheduled_at}")
                    
                    cur.execute("""
                        INSERT INTO scheduled_publications 
                        (clip_id, platform, scheduled_at, status, title, description, tags, attempts, max_attempts)
                        VALUES (%s, %s, %s, 'pending', %s, %s, %s, 0, 3)
                        ON CONFLICT DO NOTHING
                    """, (clip_id, platform, scheduled_at, clip_title, main_desc, hashtags))
            
        conn.commit()
        print(f"\n[SUCCESS] Orchestration completed successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] Orchestration error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    orchestrate_daily_publications()
