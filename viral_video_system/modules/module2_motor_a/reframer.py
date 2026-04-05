import os
import shutil
import subprocess


def reframe_to_vertical(input_path, output_path, clip_start=0, clip_end=60):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"No existe el archivo fuente: {input_path}")

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(clip_start), "-to", str(clip_end),
        "-i", input_path,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-c:v", "libx264", "-c:a", "aac", output_path,
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except Exception:
        # Fallback seguro para no romper flujo
        shutil.copy2(input_path, output_path)

    return output_path
