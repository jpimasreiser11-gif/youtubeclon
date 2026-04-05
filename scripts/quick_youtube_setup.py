"""
Quick setup script - Gets user_id and runs YouTube OAuth
"""
import psycopg2
import subprocess
import sys

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'database': 'antigravity',
    'user': 'n8n',
    'password': 'n8n'
}

try:
    # Get user_id from database
    print("📊 Getting user ID from database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users LIMIT 1")
    result = cursor.fetchone()
    
    if not result:
        print("❌ No users found in database. Please create a user first.")
        sys.exit(1)
    
    user_id = str(result[0])
    print(f"✅ Found user ID: {user_id}")
    
    cursor.close()
    conn.close()
    
    # Run YouTube OAuth setup
    print("\n🔐 Starting YouTube OAuth setup...")
    print("📱 Your browser will open in a moment...")
    print("⚠️  Approve the permissions to allow video uploads\n")
    
    client_secrets_path = r"c:\Users\jpima\Downloads\client_secret_2_102669875588-3ktbptnbmdt0q1cbc1c2e69221efhpjr.apps.googleusercontent.com.json"
    
    cmd = [
        sys.executable,  # Use current Python interpreter
        'scripts/youtube_auth_setup.py',
        '--client-secrets', client_secrets_path,
        '--user-id', user_id,
        '--db-password', 'n8n'
    ]
    
    # Run the OAuth setup
    subprocess.run(cmd, check=True)
    
    print("\n" + "=" * 50)
    print("✅ All done! YouTube is configured!")
    print("🎉 You can now upload videos automatically")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
