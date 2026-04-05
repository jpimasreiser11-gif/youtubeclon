import psycopg2

conn = psycopg2.connect(user='n8n', password='n8n', host='127.0.0.1', port=5432, database='antigravity')
cur = conn.cursor()

print("=== CLIPS COLUMNS ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'clips' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r[0]:30s} {r[1]}")

print("\n=== PROJECTS COLUMNS ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'projects' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r[0]:30s} {r[1]}")

print("\n=== RECENT PROJECTS ===")
cur.execute("SELECT id, project_status, user_id FROM projects ORDER BY created_at DESC LIMIT 3")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== SAMPLE CLIP (first row, all cols) ===")
cur.execute("SELECT * FROM clips LIMIT 1")
if cur.description:
    cols = [d[0] for d in cur.description]
    print(f"  Columns: {cols}")
    row = cur.fetchone()
    if row:
        for c, v in zip(cols, row):
            print(f"  {c:30s} = {repr(v)[:80]}")
    else:
        print("  (no rows)")

conn.close()
