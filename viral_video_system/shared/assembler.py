import os
import shutil
import subprocess


def assemble_final_video(video_path, subtitles_path, output_path, dry_run=True):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if dry_run:
        if os.path.exists(video_path):
            shutil.copy2(video_path, output_path)
        else:
            with open(output_path + ".txt", "w", encoding="utf-8") as f:
                f.write(f"dry-run output with subtitles={subtitles_path}\n")
        return output_path

    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"subtitles={subtitles_path}:force_style='FontName=Arial,FontSize=22,Bold=1,Outline=3,MarginV=200',scale=1080:1920",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
        output_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except Exception:
        shutil.copy2(video_path, output_path)

    return output_path
