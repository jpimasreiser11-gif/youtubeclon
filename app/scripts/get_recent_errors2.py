import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, dbname='antigravity', user='n8n', password='n8n')
cur = conn.cursor()
cur.execute("SELECT id, title, project_status, progress_percent, current_step, error_log FROM projects ORDER BY created_at DESC LIMIT 3;")
rows = cur.fetchall()
for r in rows:
    print(f"ID: {r[0]}\nTitle: {r[1]}\nStatus: {r[2]}\nProgress %: {r[3]}\nStep: {r[4]}\nError: {r[5]}\n-----")
cur.close()
conn.close()
