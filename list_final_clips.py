import psycopg2
conn = psycopg2.connect(host='127.0.0.1', dbname='antigravity', user='n8n', password='n8n')
c = conn.cursor()
c.execute("SELECT id, title_generated, created_at FROM clips WHERE project_id = '0403dd6b-3874-4b35-8dbd-3abf3862ba7c' ORDER BY created_at ASC")
rows = c.fetchall()
print(f"Project ID: 0403dd6b-3874-4b35-8dbd-3abf3862ba7c")
print(f"Total Clips: {len(rows)}")
for r in rows:
    print(f"  Clip ID: {r[0]} | Title: {r[1]}")
conn.close()
