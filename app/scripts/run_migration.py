import psycopg2, sys

conn = psycopg2.connect(user='n8n', password='n8n', host='127.0.0.1', port=5432, database='antigravity')
cur = conn.cursor()
print("Connected OK")

steps = [
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS progress_percent INTEGER DEFAULT 0",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS eta_seconds INTEGER DEFAULT 0",
    "ALTER TABLE projects ADD COLUMN IF NOT EXISTS current_step TEXT DEFAULT NULL",
    "UPDATE projects SET progress_percent = progress WHERE progress_percent = 0 AND progress IS NOT NULL",
    "UPDATE projects SET eta_seconds = estimated_time_remaining WHERE eta_seconds = 0 AND estimated_time_remaining IS NOT NULL",
]
for sql in steps:
    cur.execute(sql)
    print(f"OK: {sql[:70]}")

conn.commit()

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='projects' ORDER BY ordinal_position")
print("COLUMNS:", [r[0] for r in cur.fetchall()])

cur.execute("SELECT id, project_status, progress_percent FROM projects WHERE user_id='e7b33fe8-2a49-45be-99c8-181d064d5e1b' LIMIT 5")
rows = cur.fetchall()
print(f"PROJECTS for mock user ({len(rows)} found):", rows)

cur.close()
conn.close()
print("MIGRATION COMPLETE")
