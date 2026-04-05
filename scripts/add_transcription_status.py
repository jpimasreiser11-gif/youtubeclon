import psycopg2
import sys

try:
    conn = psycopg2.connect(
        host="localhost",
        database="antigravity",
        user="n8n",
        password="n8n"
    )
    cursor = conn.cursor()
    
    print("Adding transcription_status column to clips table...")
    
    # Add the column
    cursor.execute("""
        ALTER TABLE clips 
        ADD COLUMN IF NOT EXISTS transcription_status VARCHAR(50) DEFAULT 'pending'
    """)
    
    conn.commit()
    print("✅ Column added successfully!")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
