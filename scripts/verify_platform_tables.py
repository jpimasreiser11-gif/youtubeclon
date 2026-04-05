"""Ensure platform_connections has the right constraints for UPSERT"""
import psycopg2

DB = dict(user='n8n', password='n8n', host='127.0.0.1', port=5432, database='antigravity')

conn = psycopg2.connect(**DB)
cur = conn.cursor()

# Check if platform_connections has UNIQUE constraint on (user_id, platform)
cur.execute("""
    SELECT constraint_name FROM information_schema.table_constraints 
    WHERE table_name = 'platform_connections' AND constraint_type = 'UNIQUE'
""")
constraints = cur.fetchall()
print(f"Existing UNIQUE constraints: {constraints}")

if not constraints:
    try:
        cur.execute("""
            ALTER TABLE platform_connections 
            ADD CONSTRAINT platform_connections_user_platform_unique 
            UNIQUE (user_id, platform)
        """)
        conn.commit()
        print("Added UNIQUE constraint on (user_id, platform)")
    except Exception as e:
        conn.rollback()
        print(f"Constraint error (may already exist): {e}")

# Verify columns
cur.execute("""
    SELECT column_name, data_type FROM information_schema.columns 
    WHERE table_name = 'platform_connections' ORDER BY ordinal_position
""")
for col in cur.fetchall():
    print(f"  {col[0]}: {col[1]}")

# Also check platform_credentials
cur.execute("""
    SELECT column_name, data_type FROM information_schema.columns 
    WHERE table_name = 'platform_credentials' ORDER BY ordinal_position
""")
print("\nplatform_credentials columns:")
for col in cur.fetchall():
    print(f"  {col[0]}: {col[1]}")

cur.close()
conn.close()
print("\nDone!")
