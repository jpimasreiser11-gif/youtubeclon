import shutil
import subprocess


def apply_video_transformations(input_path, output_path, dry_run=True):
    if dry_run:
        shutil.copy2(input_path, output_path)
        return output_path

    filters = [
        "scale=1082:1924,crop=1080:1920:1:2",
        "setpts=0.99*PTS",
        "eq=brightness=0.02:contrast=1.01",
        "scale=1080:1920",
    ]
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-ss", "0.5",
        "-vf", ",".join(filters),
        "-af", "atempo=1.01",
        "-c:v", "libx264", "-preset", "fast",
        output_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except Exception:
        shutil.copy2(input_path, output_path)
    return output_path
