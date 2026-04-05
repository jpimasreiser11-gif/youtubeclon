"""
Upload Scheduler - Executes pending uploads to TikTok and YouTube
Runs every 5 minutes via Task Scheduler
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import psycopg2
import subprocess
import time
import os

# FIX: Forzar UTF-8 en Windows para evitar UnicodeEncodeError con emojis
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass


PROJECT_ROOT = str(Path(__file__).parent.parent.absolute())
STORAGE_BASE = os.path.join(PROJECT_ROOT, "app", "storage")

def get_pending_uploads(db_config: dict):
    """Get uploads that are due to be published"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        # Get uploads scheduled for now or earlier, not yet completed
        cursor.execute("""
            SELECT 
                sp.id, sp.clip_id, sp.platform, sp.scheduled_at,
                sp.attempts, sp.max_attempts,
                sp.title, sp.description, sp.tags,
                p.id as project_id, p.user_id
            FROM scheduled_publications sp
            JOIN clips c ON sp.clip_id = c.id
            JOIN projects p ON c.project_id = p.id
            WHERE sp.status = 'pending'
            AND sp.scheduled_at <= NOW()
            AND sp.attempts < sp.max_attempts
            ORDER BY sp.scheduled_at ASC
            LIMIT 10
        """)
        
        uploads = []
        for row in cursor.fetchall():
            uploads.append({
                'id': str(row[0]),
                'clip_id': str(row[1]),
                'platform': row[2],
                'scheduled_at': row[3],
                'attempts': row[4],
                'max_attempts': row[5],
                'title': row[6],
                'description': row[7],
                'tags': row[8],
                'project_id': str(row[9]),
                'user_id': str(row[10])
            })
        
        return uploads
        
    finally:
        cursor.close()
        conn.close()

def get_credentials(user_id: str, platform: str, db_config: dict):
    """Get platform credentials for user"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT credentials_type, credentials_data
            FROM platform_credentials
            WHERE platform = %s AND user_id = %s AND is_active = true
            LIMIT 1
        """, (platform, user_id))
        
        result = cursor.fetchone()
        if not result:
            return None
        
        return {
            'type': result[0],
            'data': result[1]
        }
        
    finally:
        cursor.close()
        conn.close()

def update_upload_status(upload_id: str, status: str, db_config: dict, error=None, video_url=None, video_id=None):
    """Update upload status in database"""
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        updates = {
            'status': status,
            'attempts': 'attempts + 1'
        }
        
        if error:
            updates['error_message'] = error
        
        if video_url:
            updates['video_url'] = video_url
        
        if status == 'uploading':
            updates['started_at'] = 'NOW()'
        elif status in ('success', 'failed', 'cancelled'):
            updates['completed_at'] = 'NOW()'
        
        set_clause = ', '.join([
            f"{k} = {v}" if v in ('attempts + 1', 'NOW()') else f"{k} = %({k})s"
            for k, v in updates.items()
        ])
        
        values = {k: v for k, v in updates.items() if v not in ('attempts + 1', 'NOW()')}
        
        cursor.execute(f"""
            UPDATE scheduled_publications
            SET {set_clause}
            WHERE id = %(upload_id)s
        """, {**values, 'upload_id': upload_id})
        
        conn.commit()
        
    finally:
        cursor.close()
        conn.close()

def log_upload(upload_id: str, level: str, message: str, db_config: dict, details=None):
    """Log upload activity"""
    print(f"[{level.upper()}] {message}")
    if details: print(f"Details: {details}")

def execute_tiktok_upload(upload: dict, credentials: dict, video_path: str, db_config: dict):
    """Execute TikTok upload using cookies"""
    upload_id = upload['id']
    
    log_upload(upload_id, 'info', f'Starting TikTok upload: {upload["title"]}', db_config)
    
    # Save cookies to temp file
    cookies_path = f'temp_cookies_{upload_id}.txt'
    with open(cookies_path, 'w', encoding='utf-8') as f:
        f.write(credentials['data'].get('cookies', ''))
    
    try:
        # Use upload_with_fallback.py
        cmd = [
            'python', os.path.join(PROJECT_ROOT, 'scripts', 'upload_with_fallback.py'),
            video_path,
            upload['title'],
            "--tags", f"{upload['description']} {upload['tags']}"
        ]
        
        # Set cookies env or pass as arg
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            # Result could contain JSON or plain text
            try:
                output = json.loads(result.stdout)
            except:
                output = {'success': 'Result:' in result.stdout}

            if output.get('success'):
                log_upload(upload_id, 'info', 'TikTok upload successful', db_config, output)
                update_upload_status(
                    upload_id, 'success', db_config,
                    video_url=output.get('video_url'),
                    video_id=output.get('video_id')
                )
                return True
            else:
                raise Exception(output.get('error', result.stdout))
        else:
            raise Exception(result.stderr)
            
    except Exception as e:
        error_msg = str(e)
        log_upload(upload_id, 'error', f'TikTok upload failed: {error_msg}', db_config)
        
        # Check if max attempts reached
        if upload['attempts'] + 1 >= upload['max_attempts']:
            update_upload_status(upload_id, 'failed', db_config, error=error_msg)
        else:
            update_upload_status(upload_id, 'pending', db_config, error=error_msg)
        
        return False
        
    finally:
        # Cleanup temp cookies
        if Path(cookies_path).exists():
            Path(cookies_path).unlink()

def execute_youtube_upload(upload: dict, credentials: dict, video_path: str, db_config: dict):
    """Execute YouTube upload using OAuth"""
    upload_id = upload['id']
    
    log_upload(upload_id, 'info', f'Starting YouTube upload: {upload["title"]}', db_config)
    
    try:
        # Use google-auth library
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        
        # Create credentials from stored data
        creds_data = credentials['data']
        creds = Credentials(
            token=creds_data.get('access_token'),
            refresh_token=creds_data.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=creds_data.get('client_id'),
            client_secret=creds_data.get('client_secret')
        )
        
        # Build YouTube service
        youtube = build('youtube', 'v3', credentials=creds)
        
        # Upload video
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        
        request = youtube.videos().insert(
            part='snippet,status',
            body={
                'snippet': {
                    'title': upload['title'][:100], # YouTube limit
                    'description': f"{upload['description']}\n\n{upload['tags']} #Shorts",
                    'tags': upload['tags'].replace('#', '').split(),
                    'categoryId': '22'  # People & Blogs
                },
                'status': {
                    'privacyStatus': 'public',
                    'selfDeclaredMadeForKids': False
                }
            },
            media_body=media
        )
        
        response = request.execute()
        
        video_id = response['id']
        video_url = f"https://youtube.com/shorts/{video_id}"
        
        log_upload(upload_id, 'info', 'YouTube upload successful', db_config, response)
        update_upload_status(upload_id, 'success', db_config, video_url=video_url, video_id=video_id)
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        log_upload(upload_id, 'error', f'YouTube upload failed: {error_msg}', db_config)
        
        if upload['attempts'] + 1 >= upload['max_attempts']:
            update_upload_status(upload_id, 'failed', db_config, error=error_msg)
        else:
            update_upload_status(upload_id, 'pending', db_config, error=error_msg)
        
        return False

def run_scheduler(db_config: dict):
    """Main scheduler loop"""
    print(f"Upload Scheduler started at {datetime.now()}")
    
    # Get pending uploads
    uploads = get_pending_uploads(db_config)
    
    if not uploads:
        print("[SUCCESS] No pending uploads")
        return
    
    print(f"[INFO] Found {len(uploads)} pending uploads")
    
    for upload in uploads:
        print(f"\n[RUN] Processing: {upload['title']} -> {upload['platform']}")
        
        # Update to uploading
        update_upload_status(upload['id'], 'uploading', db_config)
        
        # Get video path
        video_path = os.path.join(STORAGE_BASE, "subtitled", f"{upload['clip_id']}.mp4")
        if not Path(video_path).exists():
            video_path = os.path.join(STORAGE_BASE, "clips", f"{upload['clip_id']}.mp4")
        if not Path(video_path).exists():
            video_path = os.path.join(STORAGE_BASE, "previews", f"{upload['clip_id']}.mp4")
        
        if not Path(video_path).exists():
            print(f"[ERROR] Video not found: {video_path}")
            update_upload_status(upload['id'], 'failed', db_config, error='Video file not found')
            continue
        
        # Get credentials
        credentials = get_credentials(upload['user_id'], upload['platform'], db_config)
        
        if not credentials:
            print(f"[ERROR] No credentials found for {upload['platform']}")
            update_upload_status(upload['id'], 'failed', db_config, error='Credentials not found')
            continue
        
        # Execute upload
        if upload['platform'] == 'tiktok':
            success = execute_tiktok_upload(upload, credentials, video_path, db_config)
        elif upload['platform'] == 'youtube':
            success = execute_youtube_upload(upload, credentials, video_path, db_config)
        else:
            print(f"[ERROR] Unsupported platform: {upload['platform']}")
            continue
        
        if success:
            print(f"[SUCCESS] Upload successful!")
        else:
            print(f"[ERROR] Upload failed")
        
        # Small delay between uploads
        time.sleep(5)
    
    print(f"\n[SUCCESS] Scheduler completed at {datetime.now()}")

def main():
    parser = argparse.ArgumentParser(description="Upload Scheduler")
    parser.add_argument('--db-host', default='localhost')
    parser.add_argument('--db-name', default='antigravity')
    parser.add_argument('--db-user', default='postgres')
    parser.add_argument('--db-password', required=True)
    
    args = parser.parse_args()
    
    db_config = {
        'host': args.db_host,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }
    
    try:
        run_scheduler(db_config)
    except Exception as e:
        print(f"[ERROR] Scheduler error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
