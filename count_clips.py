import psycopg2
conn = psycopg2.connect(host='127.0.0.1', dbname='antigravity', user='n8n', password='n8n')
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM clips WHERE project_id = '0403dd6b-3874-4b35-8dbd-3abf3862ba7c'")
print(f"Clips found: {c.fetchone()[0]}")
conn.close()
