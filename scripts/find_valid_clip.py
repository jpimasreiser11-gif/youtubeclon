import psycopg2
import sys

# Project ID that DEFINITELY exists as a file
project_id = '8c3896d8-61c8-43cc-ba7b-23a084a2e496'

try:
    conn = psycopg2.connect(
        host="localhost",
        database="antigravity",
        user="n8n",
        password="n8n"
    )
    cur = conn.cursor()
    # Find ANY clip for this project
    cur.execute("SELECT id FROM clips WHERE project_id = %s LIMIT 1", (project_id,))
    res = cur.fetchone()
    if res:
        print(res[0])
    else:
        print("NO_CLIPS_FOUND")
    conn.close()
except Exception as e:
    print(e)
