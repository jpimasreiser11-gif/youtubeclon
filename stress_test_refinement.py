import json
import os
import subprocess
import numpy as np

def run_stress_test():
    print("🚀 Starting Segment Refinement Stress Test...")
    
    # CASE 1: Perfect Alignment Target
    # Original boundaries are in the middle of words, but there's a perfect punctuation + silence point nearby
    clips_1 = [{"title": "Perfect Align", "start_time": 10.0, "end_time": 20.0}]
    words_1 = [
        {"word": "Start.", "start": 9.4, "end": 9.5},  # Punctuation at 9.5
        {"word": "End?", "start": 20.4, "end": 20.5}   # Punctuation at 20.5
    ]
    silences_1 = {"boundary_points": [9.5, 20.5]}
    
    # CASE 2: Minimum Duration Enforcement
    # The "best" boundaries would make the clip 3 seconds, but we enforce 5s+
    clips_2 = [{"title": "Min Duration", "start_time": 30.0, "end_time": 33.0}]
    words_2 = []
    
    # CASE 3: Visual Cut Priority
    # No punctuation, but a hard camera cut at 40.0
    clips_3 = [{"title": "Visual Cut", "start_time": 40.5, "end_time": 50.0}]
    visual_cuts_mock = [40.0] 
    
    # Run tests
    test_data = [
        ("test_1", clips_1, words_1, silences_1),
        ("test_2", clips_2, words_2, {})
    ]
    
    for name, c, w, s in test_data:
        fn_c, fn_w, fn_s, fn_o = f"{name}_c.json", f"{name}_w.json", f"{name}_s.json", f"{name}_o.json"
        with open(fn_c, 'w') as f: json.dump(c, f)
        with open(fn_w, 'w') as f: json.dump(w, f)
        with open(fn_s, 'w') as f: json.dump(s, f)
        
        cmd = [
            r"c:\Users\jpima\Downloads\edumind---ai-learning-guide\venv_sovereign\Scripts\python.exe",
            "scripts/refine_segments.py",
            "--clips", fn_c,
            "--words", fn_w,
            "--silences", fn_s,
            "--output", fn_o
        ]
        subprocess.run(cmd, check=True)
        
        with open(fn_o, 'r') as f:
            res = json.load(f)
            print(f"\n📊 Result for {name}:")
            print(json.dumps(res, indent=2))
        
        # Cleanup
        for fn in [fn_c, fn_w, fn_s, fn_o]: os.remove(fn)

if __name__ == "__main__":
    run_stress_test()
