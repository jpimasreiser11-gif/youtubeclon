"""
YouTube OAuth Setup Script
Obtains refresh token and saves to database
"""
import sys
import json
import argparse
from pathlib import Path
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import psycopg2
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
from dotenv import load_dotenv

# Load environment variables
root_dir = Path(__file__).parent.parent
env_path = root_dir / 'app' / '.env'
load_dotenv(dotenv_path=env_path)

# OAuth scopes needed
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly'
]

# Redirect URI (must match Google Cloud Console)
REDIRECT_URI = 'http://localhost:3001/api/auth/callback/google'

from datetime import datetime

# Setup logging
log_file = Path('c:/Users/jpima/Downloads/edumind---ai-learning-guide/youtube_auth.log')
def log(msg):
    try:
        # Cast to string to be safe
        now = datetime.now().strftime('%H:%M:%S')
        msg_str = f"[{now}] {str(msg)}"
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{msg_str}\n")
        # Use safe print for Windows
        sys.stdout.buffer.write((msg_str + "\n").encode('utf-8'))
        sys.stdout.flush()
    except:
        pass # Better silence than crash in auth setup

class CallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback"""
    
    def do_GET(self):
        """Handle GET request from OAuth callback"""
        log(f"--- Received request: {self.path}")
        
        # Parse query parameters
        query_components = parse_qs(urlparse(self.path).query)
        
        if 'code' in query_components:
            self.server.auth_code = query_components['code'][0]
            log("[OK] Code found in request!")
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <html>
            <head>
                <meta http-equiv="refresh" content="2;url=http://localhost:3000/connections?youtube=success">
                <style>
                    body { font-family: 'Inter', system-ui, sans-serif; background: #0a0a0a; color: white; text-align: center; padding-top: 100px; }
                    .card { background: #111; border: 1px solid #1f1f1f; display: inline-block; padding: 40px; border-radius: 20px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
                    .icon { font-size: 50px; margin-bottom: 20px; }
                    h1 { color: #10b981; margin-bottom: 10px; }
                    p { color: #71717a; }
                    .btn { display: inline-block; margin-top: 20px; color: #f97316; text-decoration: none; font-weight: bold; border: 1px solid #f97316; padding: 10px 20px; border-radius: 8px; transition: all 0.2s; }
                    .btn:hover { background: #f97316; color: white; }
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="icon">SUCCESS</div>
                    <h1>Autorizacion Exitosa!</h1>
                    <p>Tus credenciales de YouTube se han guardado de forma segura.</p>
                    <p>Seras redirigido a la aplicacion en un momento...</p>
                    <a href="http://localhost:3000/connections" class="btn">Volver al Dashboard</a>
                </div>
                <script>setTimeout(() => { window.location.href = 'http://localhost:3000/connections?youtube=success'; }, 2500);</script>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
        else:
            log("[FAIL] No code found in this request (might be favicon or other)")
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Waiting for auth code...")
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass

def get_oauth_token(client_secrets_file: str):
    """Run OAuth flow to get refresh token"""
    log("[START] Starting OAuth Token Flow")
    
    # Create flow
    flow = Flow.from_client_secrets_file(
        client_secrets_file,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    log(f"[AUTH] Auth URL: {auth_url}")
    
    # Open browser if not explicitly disabled
    if not getattr(get_oauth_token, 'no_browser', False):
        log("[BROWSER] Opening browser...")
        webbrowser.open(auth_url)
    else:
        log("[BROWSER] Browser opening skipped (--no-browser)")
    
    # Start local server to receive callback
    log("[SERVER] Starting HTTP listener on port 3001 (0.0.0.0)")
    # Bind to 0.0.0.0 to listen on all IPv4 interfaces
    try:
        server = HTTPServer(('0.0.0.0', 3001), CallbackHandler)
    except Exception as e:
        log(f"[ERROR] Failed to start server: {e}")
        raise
        
    server.auth_code = None
    
    # Handle requests until we get a code (some browsers make noise requests)
    log("[WAIT] Waiting for callback...")
    while not server.auth_code:
        try:
            server.handle_request()
        except Exception as e:
            log(f"[WARN] Request error: {e}")
    
    log(f"[OK] Authorization code received: {server.auth_code[:10]}...")
    
    # Exchange code for credentials
    log("[AUTH] Exchanging auth code for refresh token...")
    try:
        flow.fetch_token(code=server.auth_code)
        log("[AUTH] Token exchange successful")
    except Exception as e:
        log(f"[AUTH_ERROR] Token exchange failed: {e}")
        raise
        
    credentials = flow.credentials
    
    # Fetch channel info
    account_name = "YouTube Channel"
    try:
        log("[AUTH] Fetching channel info...")
        youtube = build('youtube', 'v3', credentials=credentials)
        channels_response = youtube.channels().list(
            part='snippet',
            mine=True
        ).execute()
        
        if channels_response.get('items'):
            account_name = channels_response['items'][0]['snippet']['title']
            log(f"[AUTH] Found channel: {account_name}")
    except Exception as e:
        log(f"[AUTH_WARN] Could not fetch channel name: {e}")
        
    return credentials, account_name

def save_credentials_to_db(credentials, user_id: str, account_name: str, client_id: str, client_secret: str, db_config: dict):
    """Save OAuth credentials to database"""
    log(f"[DB] Attempting to save credentials for user {user_id} ({account_name})")
    
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
    except Exception as e:
        log(f"[DB_ERROR] Failed to connect to database: {e}")
        return

    try:
        credentials_data = {
            'access_token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': client_id,
            'client_secret': client_secret,
            'scopes': credentials.scopes
        }
        
        # Check if exists (with explicit UUID cast)
        cursor.execute("""
            SELECT id FROM platform_credentials
            WHERE user_id = %s::uuid AND platform = 'youtube'
        """, (user_id,))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update
            cursor.execute("""
                UPDATE platform_credentials
                SET credentials_data = %s::jsonb,
                    account_name = %s,
                    is_active = true,
                    expires_at = NOW() + INTERVAL '60 days',
                    updated_at = NOW()
                WHERE user_id = %s::uuid AND platform = 'youtube'
            """, (json.dumps(credentials_data), account_name, user_id))
            
            log(f"[DB] Updated YouTube credentials for user {user_id}")
        else:
            # Insert
            cursor.execute("""
                INSERT INTO platform_credentials (user_id, platform, credentials_type, credentials_data, account_name, expires_at)
                VALUES (%s::uuid, 'youtube', 'oauth', %s::jsonb, %s, NOW() + INTERVAL '60 days')
            """, (user_id, json.dumps(credentials_data), account_name))
            
            log(f"[DB] Saved YouTube credentials for user {user_id}")
        
        conn.commit()
        log("[DB] Transaction committed successfully")
        
        log(f"[AUTH_DETAILS] Refresh Token: {credentials.refresh_token[:10]}...") 
        log(f"[AUTH_DETAILS] Access Token: {credentials.token[:10]}...")
        
    except Exception as e:
        log(f"[DB_ERROR] Failed to save to database: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Setup YouTube OAuth")
    parser.add_argument('--client-secrets', required=True, help='Path to client_secret.json file')
    parser.add_argument('--user-id', required=True, help='User UUID')
    parser.add_argument('--db-host', default='localhost')
    parser.add_argument('--db-name', default='antigravity')
    parser.add_argument('--db-user', default='n8n')
    parser.add_argument('--db-password', required=True)
    parser.add_argument('--db-port', default='5432')
    parser.add_argument('--no-browser', action='store_true', help='Do not open browser automatically')
    
    args = parser.parse_args()
    
    # Set the flag on the function as a hack to avoid changing signature everywhere
    get_oauth_token.no_browser = args.no_browser
    
    db_config = {
        'host': args.db_host,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password,
        'port': args.db_port
    }
    
    try:
        # Read client secrets to get client_id and client_secret
        with open(args.client_secrets, 'r') as f:
            secrets = json.load(f)
        
        if 'web' in secrets:
            client_id = secrets['web']['client_id']
            client_secret = secrets['web']['client_secret']
        elif 'installed' in secrets:
            client_id = secrets['installed']['client_id']
            client_secret = secrets['installed']['client_secret']
        else:
            raise Exception("Invalid client_secrets.json format")
        
        log("YouTube OAuth Setup")
        log("=" * 50)
        
        # Run OAuth flow
        credentials, account_name = get_oauth_token(args.client_secrets)
        
        # Save to database
        save_credentials_to_db(credentials, args.user_id, account_name, client_id, client_secret, db_config)
        
        log("\n" + "=" * 50)
        log("[OK] YouTube OAuth setup complete!")
        log("\n[INFO] You can now upload videos to YouTube automatically")
        
    except Exception as e:
        log(f"\n[ERROR] Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
