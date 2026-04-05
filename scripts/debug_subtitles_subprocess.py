import subprocess
import os

python_exe = r"venv_sovereign\Scripts\python.exe"
script_path = r"scripts\render_with_subtitles.py"
video_path = r"app\storage\clips\44c605f9-882e-4bc8-b82a-9a101299b452.mp4"
output_path = r"app\storage\subtitled\44c605f9-882e-4bc8-b82a-9a101299b452.mp4"
clip_id = "44c605f9-882e-4bc8-b82a-9a101299b452"

cmd = [
    python_exe,
    script_path,
    "--video", video_path,
    "--output", output_path,
    "--clip-id", clip_id,
    "--style", "hormozi",
    "--db-host", "127.0.0.1",
    "--db-password", "n8n",
    "--db-name", "antigravity",
    "--db-user", "n8n"
]

print(f"Running command: {' '.join(cmd)}")
result = subprocess.run(cmd)

print(f"\nExit code: {result.returncode}")
