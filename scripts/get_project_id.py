import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="localhost",
        database="antigravity",
        user="n8n",
        password="n8n"
    )
    cur = conn.cursor()
    cur.execute("SELECT project_id FROM clips WHERE id = '24d43931-ffed-4911-a2a3-0455c71901c8'")
    res = cur.fetchone()
    if res:
        print(res[0])
    else:
        print("NOT_FOUND")
    conn.close()
except Exception as e:
    print(e)
