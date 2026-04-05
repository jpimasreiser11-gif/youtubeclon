import json
import os
from pathlib import Path

log_path = Path('app/logs/combined.log')
if not log_path.exists():
    print("Log not found")
    exit(1)

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if '"error":"Command failed' in line:
            # Try to find the start and end of this JSON line manually if it's mixed
            start = line.find('{')
            end = line.rfind('}')
            if start != -1 and end != -1:
                try:
                    data = json.loads(line[start:end+1])
                    if 'error' in data:
                        err = data['error']
                        # Split by carriage return and newline
                        parts = []
                        for slice in err.split('\n'):
                            for sub in slice.split('\r'):
                                if sub.strip():
                                    parts.append(sub.strip())
                        
                        print("\n=== EXTRACTED ERROR ===")
                        # Show some lines before the end
                        for p in parts[-15:]:
                            print(p)
                except Exception as e:
                    print(f"JSON Parse Error on a match: {e}")
