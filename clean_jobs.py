import psycopg2, os
from dotenv import load_dotenv
load_dotenv('app/.env')
conn=psycopg2.connect(dbname=os.getenv('POSTGRES_DB','antigravity'), user=os.getenv('POSTGRES_USER','n8n'), password=os.getenv('POSTGRES_PASSWORD','n8n'), host='127.0.0.1')
cur=conn.cursor()
cur.execute("UPDATE projects SET project_status = 'FAILED', error_log = 'Process hung and was manually cleared' WHERE project_status IN ('QUEUED', 'PROCESSING')")
conn.commit()
print('Cleaned phantom jobs.')
