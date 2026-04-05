import shutil
import imageio_ffmpeg
import os

src = imageio_ffmpeg.get_ffmpeg_exe()
print(f"Found ffmpeg at: {src}")
dst = os.path.join("data", "ffmpeg.exe")
shutil.copy(src, dst)
print(f"Copied to: {dst}")
