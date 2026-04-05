"""
Save TikTok Cookies to Database
Reads cookies from file and stores them encrypted in DB
"""
import sys
import argparse
import psycopg2

def save_cookies_to_db(cookies_file: str, user_id: str, db_config: dict):
    """Save cookies from Netscape format file to database"""
    
    # Read cookies file
    with open(cookies_file, 'r', encoding='utf-8') as f:
        cookies_content = f.read()
    
    # Connect to database
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    try:
        # Check if credentials already exist
        cursor.execute("""
            SELECT id FROM platform_credentials
            WHERE user_id = %s AND platform = 'tiktok'
        """, (user_id,))
        
        existing = cursor.fetchone()
        
        credentials_data = {
            'cookies': cookies_content
        }
        
        if existing:
            # Update existing
            cursor.execute("""
                UPDATE platform_credentials
                SET credentials_data = %s::jsonb,
                    is_active = true,
                    updated_at = NOW()
                WHERE user_id = %s AND platform = 'tiktok'
            """, (str(credentials_data).replace("'", '"'), user_id))
            
            print(f"✅ Updated TikTok cookies for user {user_id}")
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO platform_credentials (user_id, platform, credentials_type, credentials_data)
                VALUES (%s, 'tiktok', 'cookies', %s::jsonb)
            """, (user_id, str(credentials_data).replace("'", '"')))
            
            print(f"✅ Saved new TikTok cookies for user {user_id}")
        
        conn.commit()
        
        # Show summary
        cursor.execute("""
            SELECT created_at, updated_at
            FROM platform_credentials
            WHERE user_id = %s AND platform = 'tiktok'
        """, (user_id,))
        
        row = cursor.fetchone()
        print(f"\n📊 Cookie Status:")
        print(f"   Created: {row[0]}")
        print(f"   Updated: {row[1]}")
        print(f"   ⚠️  Remember: TikTok cookies expire every ~7 days")
        
    finally:
        cursor.close()
        conn.close()

def main():
    parser = argparse.ArgumentParser(description="Save TikTok cookies to database")
    parser.add_argument('--cookies-file', required=True, help='Path to cookies.txt file')
    parser.add_argument('--user-id', required=True, help='User UUID')
    parser.add_argument('--db-host', default='localhost')
    parser.add_argument('--db-name', default='edumind_viral')
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
        save_cookies_to_db(args.cookies_file, args.user_id, db_config)
        print("\n✅ Done! Cookies saved successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
