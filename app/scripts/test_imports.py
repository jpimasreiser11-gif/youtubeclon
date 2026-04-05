import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

try:
    print("Testing imports...")
    from sovereign_core import ViralEngine
    print("✓ sovereign_core imported")
    
    import time
    print("✓ time imported")
    
    from datetime import timedelta
    print("✓ timedelta imported")
    
    print("\n✅ All imports successful!")
    
except Exception as e:
    print(f"\n❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
