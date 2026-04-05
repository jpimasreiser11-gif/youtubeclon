import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "user": "n8n",
    "password": "n8n",
    "host": "localhost",
    "port": 5432,
    "database": "antigravity"
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# Find stuck processing jobs
cur.execute("SELECT id FROM projects WHERE project_status = 'PROCESSING';")
stuck_jobs = cur.fetchall()

for (job_id,) in stuck_jobs:
    print(f"Marking job {job_id} as FAILED because it is stuck.")
    cur.execute(
        "UPDATE projects SET project_status = 'FAILED', error_log = 'El proceso se interrumpió o quedó atascado. Por favor, vuelve a intentarlo.' WHERE id = %s;",
        (job_id,)
    )

conn.commit()
cur.close()
conn.close()

import redis
r = redis.Redis(host='localhost', port=6379, db=0)
active = r.lrange('bull:video-processing:active', 0, -1)
for job in active:
    print(f"Removing stuck redis job: {job}")
    r.lrem('bull:video-processing:active', 0, job)
    r.zadd('bull:video-processing:failed', {job: 1})

print("Cleanup complete.")
