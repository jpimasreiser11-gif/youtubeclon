import os
import sys
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
import argparse
import json
import psycopg2

SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def get_authenticated_service(user_id=None, db_config=None):
    """
    Obtiene servicio de YouTube autenticado usando OAuth 2.0.
    Si se proporciona user_id, intenta cargar desde la DB.
    """
    creds = None
    token_path = f'youtube_token_{user_id}.pickle' if user_id else 'youtube_token.pickle'
    
    # 1. Intentar cargar desde archivo local (cache)
    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    # 2. Si no hay archivo o es inválido, intentar cargar desde DB si hay user_id
    if (not creds or not creds.valid) and user_id and db_config:
        print(f"🔍 Fetching credentials for user {user_id} from database...")
        try:
            conn = psycopg2.connect(**db_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT credentials_data FROM platform_credentials 
                WHERE user_id = %s AND platform = 'youtube' AND is_active = true
            """, (user_id,))
            row = cursor.fetchone()
            if row:
                data = row[0]
                from google.oauth2.credentials import Credentials
                creds = Credentials(
                    token=data.get('access_token'),
                    refresh_token=data.get('refresh_token'),
                    token_uri=data.get('token_uri'),
                    client_id=data.get('client_id'),
                    client_secret=data.get('client_secret'),
                    scopes=data.get('scopes')
                )
                print("✅ Credentials loaded from database")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"⚠️ Error fetching from DB: {e}")

    # 3. Renovación o Login manual
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"❌ Error refreshing credentials: {e}")
                # Don't fall back to interactive, just fail
                raise Exception("Credentials expired and refresh failed. Please reconnect in the app.")
        else:
            # Server-side script cannot open browser
            raise Exception("No valid credentials found. Please connect YouTube account in the app.")
            
            # Legacy code removed to prevent hanging
            # secrets_file = 'client_secrets.json'
            # if not os.path.exists(secrets_file): ...
            # flow = InstalledAppFlow...
        
        # Guardar cache local
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('youtube', 'v3', credentials=creds)

def upload_to_youtube(video_path, title, description, category='22', privacy='private', tags=None, user_id=None, db_config=None):
    """
    Sube un video a YouTube
    """
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return None
    
    print(f"Uploading to YouTube: {title}")
    
    youtube = get_authenticated_service(user_id=user_id, db_config=db_config)
    
    body = {
        'snippet': {
            'title': title,
            'description': f"{description}\n\n#Shorts",
            'tags': tags or [],
            'categoryId': category
        },
        'status': {
            'privacyStatus': privacy,
            'selfDeclaredMadeForKids': False
        }
    }
    
    # Crear media upload
    media = MediaFileUpload(
        video_path,
        chunksize=-1,
        resumable=True,
        mimetype='video/mp4'
    )
    
    # Ejecutar upload
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")
    
    video_id = response['id']
    print(f"✓ Video uploaded successfully!")
    print(f"Video ID: {video_id}")
    print(f"URL: https://www.youtube.com/watch?v={video_id}")
    
    return video_id

def schedule_youtube_upload(video_path, title, description, publish_at, tags=None, user_id=None, db_config=None):
    """
    Programa un video para publicación futura en YouTube
    """
    
    youtube = get_authenticated_service(user_id=user_id, db_config=db_config)
    
    body = {
        'snippet': {
            'title': title,
            'description': f"{description}\n\n#Shorts",
            'tags': tags or [],
            'categoryId': '22'
        },
        'status': {
            'privacyStatus': 'private',
            'publishAt': publish_at,  # YouTube publicará automáticamente en esta fecha
            'selfDeclaredMadeForKids': False
        }
    }
    
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    
    request = youtube.videos().insert(
        part=','.join(body.keys()),
        body=body,
        media_body=media
    )
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Upload progress: {int(status.progress() * 100)}%")
    
    print(f"✓ Video scheduled for {publish_at}")
    print(f"Video ID: {response['id']}")
    
    return response['id']

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload video to YouTube")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--privacy", default="private", choices=['public', 'private', 'unlisted'])
    parser.add_argument("--tags", help="Comma-separated tags")
    parser.add_argument("--schedule", help="Schedule publish time (ISO 8601 format)")
    parser.add_argument("--user-id", help="User UUID for DB credentials")
    parser.add_argument("--db-host", default="localhost")
    parser.add_argument("--db-name", default="antigravity")
    parser.add_argument("--db-user", default="n8n")
    parser.add_argument("--db-password", default="n8n")
    
    args = parser.parse_args()
    
    db_config = {
        'host': args.db_host,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }
    
    tags = args.tags.split(',') if args.tags else []
    if args.schedule:
        schedule_youtube_upload(
            args.video,
            f"{args.title} #Shorts",
            args.description,
            args.schedule,
            tags,
            user_id=args.user_id,
            db_config=db_config
        )
    else:
        upload_to_youtube(
            args.video,
            f"{args.title} #Shorts",
            args.description,
            privacy=args.privacy,
            tags=tags,
            user_id=args.user_id,
            db_config=db_config
        )
