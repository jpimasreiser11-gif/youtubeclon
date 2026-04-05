import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add app/scripts to path
ROOT_DIR = str(Path(__file__).parent.parent)
sys.path.append(os.path.join(ROOT_DIR, 'app', 'scripts'))

from broll_manager import BRollManager

def test_broll():
    load_dotenv(os.path.join(ROOT_DIR, '.env'))
    api_key = os.getenv("PEXELS_API_KEY")
    
    if not api_key:
        print("❌ No PEXELS_API_KEY found in .env")
        return

    manager = BRollManager(api_key=api_key, data_dir="data_test")
    
    keywords = ["money", "nature", "crypto", "coding"]
    
    for kw in keywords:
        print(f"\n🔍 Testing keyword: {kw}")
        path = manager.fetch_video(kw, "test_proj", 0)
        if path and os.path.exists(path):
            print(f"✅ Success! Video saved at: {path}")
            # Clean up
            # os.remove(path)
        else:
            print(f"❌ Failed to fetch video for: {kw}")

if __name__ == "__main__":
    test_broll()
