import psycopg2
import os
import sys

# Database Configuration (Standardized for Antigravity)
DB_CONFIG = {
    "user": "n8n",
    "password": "n8n",
    "host": "localhost",
    "port": 5432,
    "database": "antigravity"
}

def apply_migration():
    sql_path = os.path.join(os.path.dirname(__file__), "..", "migrations", "004_publishing_schema.sql")
    if not os.path.exists(sql_path):
        print(f"❌ Migration file not found: {sql_path}")
        return

    print(f"🚀 Applying migration 004 from {sql_path}...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            
        cur.execute(sql_content)
        conn.commit()
        
        cur.close()
        conn.close()
        print("✅ Migration 004 applied successfully.")
        
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        print("\n💡 TIP: Ensure Docker is running ('docker-compose up -d') and PostgreSQL is accessible at localhost:5432.")
        sys.exit(1)

if __name__ == "__main__":
    apply_migration()
