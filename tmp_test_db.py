import psycopg2
import json

def test_insert():
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='antigravity',
            user='n8n',
            password='n8n'
        )
        cur = conn.cursor()
        
        cur.execute("SELECT id FROM users WHERE email = 'j.pima@example.com'")
        user_id = cur.fetchone()[0]
        print(f"Found User ID: {user_id}")
        
        cur.execute("DELETE FROM platform_credentials WHERE user_id = %s AND platform = 'youtube'", (user_id,))
        
        cur.execute("""
            INSERT INTO platform_credentials (user_id, platform, credentials_type, credentials_data, is_active)
            VALUES (%s, 'youtube', 'oauth', %s::jsonb, true)
        """, (user_id, json.dumps({'test_access_token': 'abc', 'test_refresh_token': 'xyz'})))
        
        conn.commit()
        print(f"Successfully inserted test record for user {user_id}")
        
        cur.execute("SELECT is_active FROM platform_credentials WHERE user_id = %s AND platform = 'youtube'", (user_id,))
        print(f"Verified is_active: {cur.fetchone()[0]}")
        
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_insert()
