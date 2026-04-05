import os
import sys
from datetime import datetime

output_dir = os.path.abspath("output")
print(f"Scanning: {output_dir}")

if not os.path.exists(output_dir):
    print("Output dir does not exist!")
    sys.exit(1)

print(f"Current Time: {datetime.now()}")

found_files = []
for root, dirs, files in os.walk(output_dir):
    for file in files:
        full_path = os.path.join(root, file)
        mtime = os.path.getmtime(full_path)
        age = datetime.now().timestamp() - mtime
        if age < 86400:
            found_files.append((file, age))

found_files.sort(key=lambda x: x[1])
for file, age in found_files:
    print(f"  Found: {file} | Age: {age:.2f}s")
