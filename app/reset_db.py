import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('.env')

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    dbname=os.getenv('POSTGRES_DB', 'antigravity'),
    user=os.getenv('POSTGRES_USER', 'n8n'),
    password=os.getenv('POSTGRES_PASSWORD', 'n8n')
)
cur = conn.cursor()
cur.execute("UPDATE projects SET project_status='QUEUED', progress_percent=0, current_step='Reinicio Forzado (Evitando deadlock)', error_log=NULL WHERE id='f4ca43dd-6928-43e6-93bf-b2fdba88fdce'")
conn.commit()
print("DB Reset exitoso")
cur.close()
conn.close()
