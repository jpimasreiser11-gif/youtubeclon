from pathlib import Path

log_path = Path('app/logs/combined.log')
if not log_path.exists():
    print("Log not found")
    exit(1)

with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
    for i, line in enumerate(f, 1):
        if i == 185 or '{"attempt":1' in line:
            print(f"--- Line {i} ---")
            # Split by carriage return to see the sequence of updates
            parts = line.split('\r')
            print(f"Total parts (progress updates): {len(parts)}")
            
            # Print the first part (usually the command start)
            print("First part:")
            print(parts[0][:500])
            
            # Print the last few parts to see the error
            print("\nLast 10 parts:")
            for p in parts[-10:]:
                if p.strip():
                    print(f"PART: {p.strip()[:200]}")
