import os
import sys
import json
from rapidfuzz import fuzz

# Add scripts directories to path
sys.path.append(os.path.join(os.getcwd(), 'scripts'))
sys.path.append(os.path.join(os.getcwd(), 'app', 'scripts'))

from clipper import process_clip
from ingest import find_surgical_timestamp

def test_high_fidelity():
    print("🧪 Starting High-Fidelity Verification...")
    
    video_id = "jNQXAC9IVRw"
    video_path = f"data/{video_id}.mp4"
    if not os.path.exists(video_path):
        print(f"❌ Test video not found: {video_path}")
        return

    # 1. Test Surgical Precision (Fuzzy Matching)
    print("\n--- Testing Surgical Precision ---")
    mock_words = [
        {"word": "Welcome", "start": 0.5, "end": 1.0},
        {"word": "to", "start": 1.1, "end": 1.3},
        {"word": "this", "start": 1.4, "end": 1.6},
        {"word": "amazing", "start": 1.7, "end": 2.2},
        {"word": "video", "start": 2.3, "end": 2.8}
    ]
    
    # Target: "this amazing"
    target_start = "Welcome to"
    target_end = "amazing video"
    
    start_align = find_surgical_timestamp(mock_words, target_start, 0.4, is_end=False)
    end_align = find_surgical_timestamp(mock_words, target_end, 2.5, is_end=True)
    
    print(f"Target Start: '{target_start}' -> Aligned: {start_align:.2f}s (Expected 0.50)")
    print(f"Target End: '{target_end}' -> Aligned: {end_align:.2f}s (Expected 2.80)")
    
    # 2. Test Rendering (One Euro Filter & Stabilization)
    print("\n--- Testing Stabilization Render ---")
    # This will generate a small clip with the filter active
    try:
        process_clip(
            video_id=video_id,
            title="HF Test Clip",
            start_time=0.0,
            end_time=5.0,
            index="HF_TEST",
            all_words=mock_words,
            input_path=video_path,
            subtitle_style="HORMOZI"
        )
        print("✅ Render completed successfully (output/jNQXAC9IVRw_clip_HF_TEST.mp4)")
    except Exception as e:
        print(f"❌ Render failed: {e}")

if __name__ == "__main__":
    if not os.path.exists('output'):
        os.makedirs('output')
    test_high_fidelity()
