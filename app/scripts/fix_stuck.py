import psycopg2
conn = psycopg2.connect(user='n8n', password='n8n', host='127.0.0.1', port=5432, database='antigravity')
cur = conn.cursor()
cur.execute("UPDATE projects SET project_status = 'FAILED', updated_at = NOW() WHERE project_status = 'PROCESSING' AND updated_at < NOW() - INTERVAL '30 minutes'")
stuck = cur.rowcount
cur.execute('SELECT id, project_status, progress_percent FROM projects ORDER BY created_at DESC LIMIT 5')
rows = cur.fetchall()
conn.commit()
conn.close()
print(f'Fixed {stuck} stuck projects')
print('Latest projects:')
for r in rows:
    print(f'  {r[0]} | {r[1]} | progress={r[2]}')
