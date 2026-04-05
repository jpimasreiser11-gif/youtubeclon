import psycopg2
conn = psycopg2.connect(host='127.0.0.1', dbname='antigravity', user='n8n', password='n8n')
c = conn.cursor()
c.execute("""
    UPDATE projects 
    SET auto_publish_enabled = TRUE, 
        publish_slots_per_day = 3,
        publish_platforms = '{tiktok, youtube}'
    WHERE id = '0403dd6b-3874-4b35-8dbd-3abf3862ba7c'
""")
conn.commit()
print("Project marked for auto-publish!")
conn.close()
