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

create_table_sql = """
CREATE TABLE IF NOT EXISTS transcriptions (
    id SERIAL PRIMARY KEY,
    clip_id UUID NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
    language VARCHAR(10),
    words JSONB,
    edited BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_clip_transcription UNIQUE (clip_id)
);
"""

try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    print("Creating transcriptions table...")
    cur.execute(create_table_sql)
    conn.commit()
    print("✅ Table 'transcriptions' created successfully.")
    cur.close()
    conn.close()
except Exception as e:
    print(f"❌ Error creating table: {e}")
