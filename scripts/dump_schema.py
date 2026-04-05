import psycopg2
conn = psycopg2.connect(host='localhost', port=5432, database='antigravity', user='n8n', password='n8n')
cur = conn.cursor()
cur.execute('SELECT column_name, data_type FROM information_schema.columns WHERE table_name = \'scheduled_publications\'')
cols = cur.fetchall()
for c in cols:
    print(f"{c[0]}: {c[1]}")
cur.close()
conn.close()
