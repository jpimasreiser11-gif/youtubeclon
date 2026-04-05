import psycopg2
conn = psycopg2.connect(host='127.0.0.1', dbname='antigravity', user='n8n', password='n8n')
c = conn.cursor()
c.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'scheduled_publications'")
for r in c.fetchall():
    print(r[0])
conn.close()
