import psycopg2
conn = psycopg2.connect(host='127.0.0.1', dbname='antigravity', user='n8n', password='n8n')
c = conn.cursor()
c.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'scheduled_uploads')")
print(f"scheduled_uploads exists: {c.fetchone()[0]}")
c.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'scheduled_publications')")
print(f"scheduled_publications exists: {c.fetchone()[0]}")
conn.close()
