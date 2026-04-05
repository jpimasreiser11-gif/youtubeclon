"""
Debug script to verify clipper receives word data correctly
"""
import json
import sys

# Simulate what quick_test_pipeline passes to clipper
transcript_file = "data/jNQXAC9IVRw.json"

with open(transcript_file, 'r') as f:
    data = json.load(f)

# Import extractor
sys.path.append('scripts')
from full_pipeline import extract_words_from_segments

words = extract_words_from_segments(data.get('segments', []))

print(f"Total words extracted: {len(words)}")
print(f"\nFirst 10 words:")
for i, word in enumerate(words[:10]):
    print(f"  {i+1}. '{word['word']}' ({word['start']:.2f}s - {word['end']:.2f}s)")

print(f"\nWord data structure looks correct: {bool(words)}")

# Test filtering for a clip from 0 to 15s
from clipper import filter_words_for_clip

filtered = filter_words_for_clip(words, start_time=0.0, end_time=15.0)

print(f"\n--- Filtering test (0s - 15s) ---")
print(f"Filtered words: {len(filtered)}")
print(f"\nFirst 5 filtered words:")
for i, word in enumerate(filtered[:5]):
    print(f"  {i+1}. '{word['word']}' ({word['start']:.2f}s - {word['end']:.2f}s)")

if filtered:
    print(f"\n✅ Word filtering works correctly!")
else:
    print(f"\n❌ No words were filtered - this is the problem!")
