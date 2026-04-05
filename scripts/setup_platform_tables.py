"""Setup platform_credentials table and verify platform_connections"""
import psycopg2

DB = dict(user='n8n', password='n8n', host='127.0.0.1', port=5432, database='antigravity')

conn = psycopg2.connect(**DB)
cur = conn.cursor()

# Check platform_credentials
cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='platform_credentials')")
exists = cur.fetchone()[0]
print(f"platform_credentials exists: {exists}")

if not exists:
    cur.execute("""
        CREATE TABLE platform_credentials (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            platform VARCHAR(50) NOT NULL,
            credentials_type VARCHAR(50) DEFAULT 'oauth',
            credentials_data JSONB NOT NULL DEFAULT '{}',
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(user_id, platform)
        )
    """)
    conn.commit()
    print("Created platform_credentials table!")

# Verify platform_connections
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='platform_connections' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print(f"platform_connections columns: {cols}")

# Check for users
cur.execute("SELECT id, email FROM users LIMIT 3")
users = cur.fetchall()
for u in users:
    print(f"User: {u[0]} ({u[1]})")

cur.close()
conn.close()
print("Done!")
