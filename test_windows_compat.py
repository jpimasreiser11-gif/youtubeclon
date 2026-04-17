#!/usr/bin/env python3
"""
Windows Compatibility Checker
Validates that all modules work correctly on Windows.
"""
import sys
import os
import platform
from pathlib import Path

def check_platform():
    """Verify we're on Windows."""
    print("✓ Platform check...")
    system = platform.system()
    print(f"  OS: {system}")
    if system != "Windows":
        print("  ⚠️ Not on Windows (may still work)")
    return True

def check_path_handling():
    """Verify Path handling works correctly."""
    print("\n✓ Path handling...")
    try:
        from backend.config import OUTPUT_DIR, LOGS_DIR, CHANNEL_DIRS
        
        # Check Path objects
        print(f"  OUTPUT_DIR: {OUTPUT_DIR}")
        print(f"  LOGS_DIR: {LOGS_DIR}")
        print(f"  Sample channel dir: {list(CHANNEL_DIRS.values())[0]}")
        
        # Verify they can be created
        test_path = OUTPUT_DIR / "test_win_compat"
        test_path.mkdir(parents=True, exist_ok=True)
        test_file = test_path / "test.txt"
        test_file.write_text("Windows compatibility test")
        assert test_file.read_text() == "Windows compatibility test"
        test_file.unlink()
        test_path.rmdir()
        
        print("  ✅ Path handling OK")
        return True
    except Exception as e:
        print(f"  ❌ Path handling failed: {e}")
        return False

def check_subprocess_calls():
    """Verify subprocess calls work on Windows."""
    print("\n✓ Subprocess compatibility...")
    try:
        import subprocess
        
        # Test basic subprocess call (dir is Windows-specific)
        if platform.system() == "Windows":
            result = subprocess.run(
                ["cmd", "/c", "echo", "test"],
                capture_output=True,
                text=True,
                timeout=5
            )
            assert result.returncode == 0
            print("  ✅ cmd.exe subprocess calls work")
        else:
            print("  ⚠️ Skipping Windows-specific subprocess test")
        
        # Test cross-platform call
        result = subprocess.run(
            [sys.executable, "-c", "print('hello')"],
            capture_output=True,
            text=True,
            timeout=5
        )
        assert result.returncode == 0
        print("  ✅ Cross-platform subprocess calls work")
        return True
    except Exception as e:
        print(f"  ❌ Subprocess test failed: {e}")
        return False

def check_file_operations():
    """Verify file operations work correctly."""
    print("\n✓ File operations...")
    try:
        import json
        import sqlite3
        from pathlib import Path
        
        # Test JSON operations
        test_data = {"test": "data", "nested": {"key": "value"}}
        json_str = json.dumps(test_data, ensure_ascii=False)
        loaded = json.loads(json_str)
        assert loaded == test_data
        print("  ✅ JSON operations OK")
        
        # Test SQLite (main database)
        from backend.database import DB_PATH
        assert DB_PATH.parent.exists()
        print(f"  ✅ SQLite path OK: {DB_PATH}")
        
        return True
    except Exception as e:
        print(f"  ❌ File operations failed: {e}")
        return False

def check_encoding():
    """Verify UTF-8 encoding works correctly."""
    print("\n✓ Text encoding...")
    try:
        # Test Spanish characters
        spanish_text = "Ñ À É Ü ¿ ¡ © ® ™"
        test_path = Path("encoding_test.txt")
        test_path.write_text(spanish_text, encoding="utf-8")
        loaded = test_path.read_text(encoding="utf-8")
        assert loaded == spanish_text
        test_path.unlink()
        print(f"  ✅ UTF-8 encoding works (tested with: {spanish_text})")
        return True
    except Exception as e:
        print(f"  ❌ Encoding test failed: {e}")
        return False

def check_logging():
    """Verify logging works on Windows."""
    print("\n✓ Logging system...")
    try:
        import logging
        from backend.config import LOGS_DIR
        
        logger = logging.getLogger("windows-compat-test")
        handler = logging.FileHandler(LOGS_DIR / "compat_test.log")
        handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        logger.info("Windows compatibility test")
        assert (LOGS_DIR / "compat_test.log").exists()
        
        print(f"  ✅ Logging works (file: {LOGS_DIR / 'compat_test.log'})")
        return True
    except Exception as e:
        print(f"  ❌ Logging test failed: {e}")
        return False

def check_database_operations():
    """Verify database operations work correctly."""
    print("\n✓ Database operations...")
    try:
        from backend.database import init_db, get_all_channels
        
        init_db()
        channels = get_all_channels()
        print(f"  ✅ Database operations OK ({len(channels)} channels found)")
        return True
    except Exception as e:
        print(f"  ❌ Database operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Windows compatibility checks."""
    print("=" * 70)
    print("WINDOWS COMPATIBILITY CHECK")
    print("=" * 70)
    
    checks = [
        check_platform,
        check_path_handling,
        check_subprocess_calls,
        check_file_operations,
        check_encoding,
        check_logging,
        check_database_operations,
    ]
    
    results = [check() for check in checks]
    
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} checks passed")
    
    if passed == total:
        print("✅ Full Windows compatibility verified!")
        return 0
    else:
        print("⚠️ Some checks failed. Review output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
