
import sys
import os
from pathlib import Path

# Add project root to path (similar to ingest.py)
ROOT_DIR = str(Path(__file__).parent.parent.parent)
sys.path.append(ROOT_DIR)
sys.path.append(os.path.join(ROOT_DIR, 'app', 'scripts'))

try:
    from app.scripts.ingest import get_db_connection
    print("Successfully imported get_db_connection")
except ImportError:
    # Fallback if running from within app/scripts directly
    sys.path.append(os.path.join(ROOT_DIR, 'app'))
    from scripts.ingest import get_db_connection
    print("Successfully imported get_db_connection (fallback)")

conn = get_db_connection()
if conn:
    print("✅ Database connection successful!")
    conn.close()
    sys.exit(0)
else:
    print("❌ Database connection failed!")
    sys.exit(1)
