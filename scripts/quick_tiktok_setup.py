"""
Quick TikTok Cookies Setup
Gets user_id from DB and saves TikTok cookies automatically
"""
import psycopg2
import json
import sys
from pathlib import Path

# Database config
DB_CONFIG = {
    'host': 'localhost',
    'database': 'antigravity',
    'user': 'n8n',
    'password': 'n8n'
}

# Cookies file path
COOKIES_FILE = Path(__file__).parent.parent / 'tiktok_cookies.txt'

try:
    print("=" * 60)
    print("🎬 TikTok Cookies Setup")
    print("=" * 60)
    
    # Get user_id from database
    print("\n📊 Step 1: Getting user ID from database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users LIMIT 1")
    result = cursor.fetchone()
    
    if not result:
        print("❌ No users found in database. Please create a user first.")
        sys.exit(1)
    
    user_id = str(result[0])
    print(f"✅ Found user ID: {user_id}")
    
    # Read cookies file
    print(f"\n📂 Step 2: Reading cookies from {COOKIES_FILE.name}...")
    
    if not COOKIES_FILE.exists():
        print(f"❌ Cookies file not found at: {COOKIES_FILE}")
        print("\n💡 Make sure 'tiktok_cookies.txt' exists in the project root")
        sys.exit(1)
    
    with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
        cookies_content = f.read()
    
    print(f"✅ Read {len(cookies_content)} characters from cookies file")
    
    # Save to database
    print("\n💾 Step 3: Saving to database...")
    
    credentials_data = {
        'cookies': cookies_content
    }
    
    # Check if exists
    cursor.execute("""
        SELECT id FROM platform_credentials
        WHERE user_id = %s AND platform = 'tiktok'
    """, (user_id,))
    
    existing = cursor.fetchone()
    
    if existing:
        # Update
        cursor.execute("""
            UPDATE platform_credentials
            SET credentials_data = %s::jsonb,
                is_active = true,
                updated_at = NOW()
            WHERE user_id = %s AND platform = 'tiktok'
        """, (json.dumps(credentials_data), user_id))
        
        print("✅ Updated existing TikTok credentials")
    else:
        # Insert
        cursor.execute("""
            INSERT INTO platform_credentials (user_id, platform, credentials_type, credentials_data)
            VALUES (%s, 'tiktok', 'cookies', %s::jsonb)
        """, (user_id, json.dumps(credentials_data)))
        
        print("✅ Saved new TikTok credentials")
    
    conn.commit()
    
    # Show status
    cursor.execute("""
        SELECT created_at, updated_at
        FROM platform_credentials
        WHERE user_id = %s AND platform = 'tiktok'
    """, (user_id,))
    
    row = cursor.fetchone()
    
    print("\n" + "=" * 60)
    print("📊 Status:")
    print("=" * 60)
    print(f"✅ User ID:  {user_id}")
    print(f"✅ Platform: TikTok")
    print(f"✅ Created:  {row[0]}")
    print(f"✅ Updated:  {row[1]}")
    print("\n⚠️  Reminder: TikTok cookies expire every ~7 days")
    print("⚠️  You'll need to re-export and run this script again")
    print("\n" + "=" * 60)
    print("🎉 TikTok cookies saved successfully!")
    print("=" * 60)
    
    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
