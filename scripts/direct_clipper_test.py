"""
Direct manual test of clipper with word data
"""
import json
import subprocess
import sys

# Load the transcript with words
with open('data/jNQXAC9IVRw.json', 'r') as f:
    data = json.load(f)

# Extract words
sys.path.append('scripts')
from full_pipeline import extract_words_from_segments

words = extract_words_from_segments(data['segments'])

print(f"Extracted {len(words)} words")
print(f"First 5 words: {[w['word'] for w in words[:5]]}")

# Create clipper input
clipper_input = {
    'id': 'jNQXAC9IVRw',
    'clips': [
        {
            'title': 'Direct Test Clip',
            'start_time': 0.0,
            'end_time': 15.0
        }
    ],
    'words': words
}

print(f"\nCalling clipper with {len(words)} words...")
print(f"Clip: 0.0s - 15.0s")

# Call clipper directly
cmd = [
    'c:\\Users\\jpima\\Downloads\\edumind---ai-learning-guide\\venv_sovereign\\Scripts\\python.exe',
    'scripts/clipper.py',
    json.dumps(clipper_input)
]

print(f"\nRunning: {' '.join(cmd[:2])} <JSON_DATA>")
result = subprocess.run(cmd, capture_output=True, text=True)

print("\n" + "="*70)
print("STDOUT:")
print("="*70)
print(result.stdout)

if result.stderr:
    print("\n" + "="*70)
    print("STDERR:")
    print("="*70)
    print(result.stderr)

print("\n" + "="*70)
print(f"Exit code: {result.returncode}")
