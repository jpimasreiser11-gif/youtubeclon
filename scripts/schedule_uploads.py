"""
Scheduler for automated content uploads
Runs as a background service to check scheduled publications and upload them
"""
import os
import sys
import time
import json
import psycopg2
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
root_dir = Path(__file__).parent.parent
env_path = root_dir / 'app' / '.env'
load_dotenv(dotenv_path=env_path)

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

class UploadScheduler:
    def __init__(self, db_config):
        self.db_config = db_config
        self.check_interval = 60  # Check every minute
        
    def connect_db(self):
        return psycopg2.connect(**self.db_config)
    
    def get_pending_uploads(self):
        """Get all publications scheduled for now or earlier that haven't been processed"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT sp.id, sp.clip_id, sp.platform, sp.scheduled_at, 
                       sp.title, sp.description, sp.tags, sp.privacy,
                       c.project_id
                FROM scheduled_publications sp
                JOIN clips c ON sp.clip_id = c.id
                WHERE sp.status = 'pending' 
                AND sp.scheduled_at <= NOW()
                ORDER BY sp.scheduled_at ASC
            """)
            
            results = cursor.fetchall()
            publications = []
            
            for row in results:
                publications.append({
                    'id': row[0],
                    'clip_id': row[1],
                    'platform': row[2],
                    'scheduled_at': row[3],
                    'title': row[4],
                    'description': row[5] or '',
                    'tags': row[6] or '',
                    'privacy': row[7] or 'private',
                    'project_id': row[8]
                })
            
            return publications
            
        finally:
            cursor.close()
            conn.close()
    
    def mark_as_processing(self, publication_id):
        """Mark publication as being processed"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE scheduled_publications SET status = 'processing' WHERE id = %s",
                (publication_id,)
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    def mark_as_completed(self, publication_id, video_url=None):
        """Mark publication as successfully completed"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE scheduled_publications SET status = 'published', video_url = %s, completed_at = NOW() WHERE id = %s",
                (video_url, publication_id)
            )
            
            # Also insert into upload_history
            cursor.execute("""
                INSERT INTO upload_history (clip_id, platform, status, video_url, created_at)
                SELECT clip_id, platform, 'success', %s, NOW()
                FROM scheduled_publications
                WHERE id = %s
            """, (video_url, publication_id))
            
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    def mark_as_failed(self, publication_id, error_message):
        """Mark publication as failed"""
        conn = self.connect_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE scheduled_publications SET status = 'failed', error_message = %s WHERE id = %s",
                (error_message, publication_id)
            )
            
            # Also insert into upload_history
            cursor.execute("""
                INSERT INTO upload_history (clip_id, platform, status, error_message, created_at)
                SELECT clip_id, platform, 'failed', %s, NOW()
                FROM scheduled_publications
                WHERE id = %s
            """, (error_message, publication_id))
            
            conn.commit()
        finally:
            cursor.close()
            conn.close()
    
    def upload_to_youtube(self, publication):
        """Upload a clip to YouTube"""
        import subprocess
        
        root_dir = Path(__file__).parent.parent
        python_path = sys.executable
        upload_script = root_dir / 'scripts' / 'upload_youtube.py'
        
        video_path = root_dir / 'app' / 'storage' / 'clips' / f"{publication['clip_id']}.mp4"
        
        # Check if subtitled version exists, use that instead
        subtitled_path = root_dir / 'app' / 'storage' / 'subtitled' / f"{publication['clip_id']}.mp4"
        if subtitled_path.exists():
            video_path = subtitled_path
        
        cmd = [
            str(python_path),
            str(upload_script),
            '--video', str(video_path),
            '--title', publication['title'],
            '--description', publication['description'],
            '--privacy', publication['privacy']
        ]
        
        if publication['tags']:
            cmd.extend(['--tags', publication['tags']])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                # Try to extract video URL from output
                output = result.stdout
                video_url = None
                
                for line in output.split('\n'):
                    if 'URL:' in line or 'youtube.com/watch' in line:
                        parts = line.split('URL:')
                        if len(parts) > 1:
                            video_url = parts[1].strip()
                        break
                
                return True, video_url
            else:
                return False, result.stderr
                
        except Exception as e:
            return False, str(e)
    
    def upload_to_tiktok(self, publication):
        """Upload a clip to TikTok"""
        import subprocess
        
        root_dir = Path(__file__).parent.parent
        python_path = sys.executable
        upload_script = root_dir / 'scripts' / 'upload_with_fallback.py'
        
        video_path = root_dir / 'app' / 'storage' / 'clips' / f"{publication['clip_id']}.mp4"
        
        # Check if subtitled version exists
        subtitled_path = root_dir / 'app' / 'storage' / 'subtitled' / f"{publication['clip_id']}.mp4"
        if subtitled_path.exists():
            video_path = subtitled_path
        
        # TikTok caption = title + tags
        caption = publication['title']
        if publication['tags']:
            tags = ' '.join([f'#{tag.strip()}' for tag in publication['tags'].split(',')])
            caption = f"{caption} {tags}"
        
        cmd = [
            str(python_path),
            str(upload_script),
            str(video_path),
            caption
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
                
        except Exception as e:
            return False, str(e)
    
    def process_publication(self, publication):
        """Process a single scheduled publication"""
        print(f"\n{'='*60}")
        print(f"Processing publication #{publication['id']}")
        print(f"Platform: {publication['platform']}")
        print(f"Title: {publication['title']}")
        print(f"Scheduled: {publication['scheduled_at']}")
        print(f"{'='*60}\n")
        
        self.mark_as_processing(publication['id'])
        
        try:
            if publication['platform'] == 'youtube':
                success, result = self.upload_to_youtube(publication)
            elif publication['platform'] == 'tiktok':
                success, result = self.upload_to_tiktok(publication)
            else:
                raise ValueError(f"Unsupported platform: {publication['platform']}")
            
            if success:
                print(f"✅ Upload successful!")
                self.mark_as_completed(publication['id'], result if isinstance(result, str) else None)
            else:
                print(f"❌ Upload failed: {result}")
                self.mark_as_failed(publication['id'], str(result))
                
        except Exception as e:
            print(f"❌ Error processing publication: {e}")
            self.mark_as_failed(publication['id'], str(e))
    
    def run(self):
        """Main scheduler loop"""
        print("🚀 Upload Scheduler Started")
        print(f"Check interval: {self.check_interval} seconds\n")
        
        while True:
            try:
                publications = self.get_pending_uploads()
                
                if publications:
                    print(f"\nFound {len(publications)} pending uploads")
                    
                    for pub in publications:
                        self.process_publication(pub)
                        time.sleep(5)  # Brief pause between uploads
                else:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No pending uploads. Waiting...")
                
                time.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Scheduler stopped by user")
                break
            except Exception as e:
                print(f"❌ Error in scheduler loop: {e}")
                time.sleep(self.check_interval)

def main():
    # Database configuration from environment variables
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': int(os.getenv('POSTGRES_PORT', 5432)),
        'database': os.getenv('POSTGRES_DB', 'edumind_viral'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD', 'password')
    }
    
    scheduler = UploadScheduler(db_config)
    scheduler.run()

if __name__ == '__main__':
    main()
