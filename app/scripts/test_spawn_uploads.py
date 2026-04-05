#!/usr/bin/env python3
import os
import sys
import subprocess
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
STORAGE_BASE = os.path.join(ROOT, 'storage')
os.makedirs(os.path.join(STORAGE_BASE, 'upload_logs'), exist_ok=True)

# Use existing sample output video if present
possible_source = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'source_video.mp4'))
if not os.path.exists(possible_source):
    print('Sample source video not found:', possible_source)
    sys.exit(1)

final_path = possible_source

tiktok_script = os.path.join(os.path.dirname(__file__), 'upload_tiktok_playwright.py')
yt_script = os.path.join(os.path.dirname(__file__), 'upload_youtube_selenium.py')

clip_id = 'testclip'
delay_hours = 0

upload_logs_dir = os.path.join(STORAGE_BASE, 'upload_logs')
os.makedirs(upload_logs_dir, exist_ok=True)

tiktok_log = os.path.join(upload_logs_dir, f"{clip_id}_tiktok.log")
yt_log = os.path.join(upload_logs_dir, f"{clip_id}_youtube.log")

print('Spawning upload processes, logs ->', tiktok_log, yt_log)

with open(tiktok_log, 'a', encoding='utf-8') as tlf, open(yt_log, 'a', encoding='utf-8') as ylf:
    tlf.write(f"=== START {time.ctime()} ===\n")
    ylf.write(f"=== START {time.ctime()} ===\n")
    try:
        child_env = os.environ.copy()
        child_env['PYTHONIOENCODING'] = 'utf-8'
        tproc = subprocess.Popen([sys.executable, tiktok_script, '--video', final_path, '--caption', 'Test caption', '--delay_hours', str(delay_hours)], stdout=tlf, stderr=subprocess.STDOUT, env=child_env)
        yproc = subprocess.Popen([sys.executable, yt_script, '--video', final_path, '--title', 'Test Title', '--description', 'Test desc', '--privacy', 'unlisted', '--delay_hours', str(delay_hours)], stdout=ylf, stderr=subprocess.STDOUT, env=child_env)
        print('Spawned PIDs:', tproc.pid, yproc.pid)
    except Exception as e:
        print('Failed to spawn upload processes:', e)
        tlf.write(f'Failed to spawn: {e}\n')
        ylf.write(f'Failed to spawn: {e}\n')

print('Done.')
