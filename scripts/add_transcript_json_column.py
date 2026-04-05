import psycopg2
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../app/.env'))

db_config = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'database': os.getenv('POSTGRES_DB', 'edumind_viral'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'n8n')
}

alter_table_sql = """
ALTER TABLE clips 
ADD COLUMN IF NOT EXISTS transcript_json JSONB;
"""

try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    print("Adding transcript_json column to clips table...")
    cur.execute(alter_table_sql)
    conn.commit()
    print("✅ Column 'transcript_json' added successfully.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error altering table: {e}")
