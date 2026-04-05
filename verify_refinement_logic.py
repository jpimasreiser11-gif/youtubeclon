import json
import os
import subprocess

def test_refinement():
    # Mock data
    clips = [
        {"title": "Test Clip", "start_time": 10.0, "end_time": 20.0}
    ]
    words = [
        {"word": "Hello.", "start": 9.2, "end": 9.1}, # Punctuation before start
        {"word": "World!", "start": 19.8, "end": 20.3}, # Punctuation near end
    ]
    silences = {"boundary_points": [9.5, 20.5]}
    
    # Save mocks
    with open('test_clips.json', 'w') as f: json.dump(clips, f)
    with open('test_words.json', 'w') as f: json.dump(words, f)
    with open('test_silences.json', 'w') as f: json.dump(silences, f)
    
    # Run refiner (mocking scenedetect by not providing video)
    cmd = [
        r"c:\Users\jpima\Downloads\edumind---ai-learning-guide\venv_sovereign\Scripts\python.exe",
        "scripts/refine_segments.py",
        "--clips", "test_clips.json",
        "--words", "test_words.json",
        "--silences", "test_silences.json",
        "--output", "test_refined.json"
    ]
    
    print(f"Running refinement test: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    with open('test_refined.json', 'r') as f:
        refined = json.load(f)
        print("Refined result:")
        print(json.dumps(refined, indent=2))

if __name__ == "__main__":
    test_refinement()
