#!/usr/bin/env python3
"""
Sistema Profesional Videos IA - Hardening Validation
Tests configuration, database, and pipeline readiness.
"""
import sys
import json
from pathlib import Path

def test_imports():
    """Test that all modules import correctly."""
    print("✓ Testing imports...")
    try:
        from backend.config import PIPELINE_CONFIG, VIDEO_CONFIG, AUDIO_CONFIG
        from backend.database import init_db, get_all_channels
        from backend.pipeline.orchestrator import run_single_channel
        from backend.pipeline.script_writer import generate_script
        print("  ✅ All imports successful")
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_config_loading():
    """Test that configuration loads correctly."""
    print("\n✓ Testing configuration loading...")
    try:
        from backend.config import (
            PIPELINE_CONFIG, VIDEO_CONFIG, AUDIO_CONFIG, BROLL_CONFIG,
            SCRIPT_CONFIG, THUMBNAIL_CONFIG, YOUTUBE_CONFIG, AGENT_CONFIG
        )
        print(f"  PIPELINE_CONFIG: {PIPELINE_CONFIG}")
        print(f"  VIDEO_CONFIG: {VIDEO_CONFIG}")
        print(f"  AUDIO_CONFIG (allow_silent_fallback={AUDIO_CONFIG['allow_silent_fallback']})")
        print(f"  SCRIPT_CONFIG: {SCRIPT_CONFIG}")
        print(f"  MAX_CONCURRENT_AGENTS: {AGENT_CONFIG['max_concurrent']}")
        print("  ✅ Configuration loaded")
        return True
    except Exception as e:
        print(f"  ❌ Config load failed: {e}")
        return False

def test_database():
    """Test database initialization and channel lookup."""
    print("\n✓ Testing database...")
    try:
        from backend.database import init_db, get_all_channels, get_channel
        init_db()
        channels = get_all_channels()
        print(f"  Total channels: {len(channels)}")
        if channels:
            ch = channels[0]
            print(f"  Sample channel: {ch.get('channel_id')} → {ch.get('name')}")
            # Test get_channel
            ch_detail = get_channel(ch['id'])
            if ch_detail:
                print(f"  Channel detail loaded: {ch_detail.get('name')}")
            print("  ✅ Database OK")
            return True
        else:
            print("  ⚠️ No channels found (may need initialization)")
            return True
    except Exception as e:
        print(f"  ❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_orchestrator_imports():
    """Test orchestrator and metrics functions."""
    print("\n✓ Testing orchestrator metrics...")
    try:
        from backend.pipeline.orchestrator import (
            _generate_pipeline_summary, save_pipeline_report
        )
        
        # Test summary generation with mock data
        mock_results = [
            {
                "channel_id": "test-channel",
                "channel_name": "Test",
                "status": "ok",
                "elapsed_seconds": 42.5,
                "topic": "Test topic",
                "title": "Test title",
                "video_id": 1,
                "steps": {"script": "ok", "voice": "ok", "video": "ok"},
            }
        ]
        
        summary = _generate_pipeline_summary(mock_results)
        print(f"  Summary generated: {summary['total_channels']} channels")
        print(f"  Statuses: {summary['statuses']}")
        print("  ✅ Orchestrator metrics OK")
        return True
    except Exception as e:
        print(f"  ❌ Orchestrator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_script_writer():
    """Test script writer with hardened error handling."""
    print("\n✓ Testing script writer (error handling)...")
    try:
        from backend.config import SCRIPT_CONFIG
        from backend.pipeline.script_writer import generate_script
        
        print(f"  SCRIPT_CONFIG[hide_errors]: {SCRIPT_CONFIG['hide_errors']}")
        print(f"  SCRIPT_CONFIG[max_retries]: {SCRIPT_CONFIG['max_retries']}")
        
        # Don't actually generate (requires APIs), just verify config
        print("  ✅ Script writer config OK")
        return True
    except Exception as e:
        print(f"  ❌ Script writer test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 70)
    print("SISTEMA PROFESIONAL VIDEOS IA — HARDENING VALIDATION")
    print("=" * 70)
    
    tests = [
        test_imports,
        test_config_loading,
        test_database,
        test_orchestrator_imports,
        test_script_writer,
    ]
    
    results = [test() for test in tests]
    
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All hardening validations passed!")
        return 0
    else:
        print("⚠️ Some tests failed. Review output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
