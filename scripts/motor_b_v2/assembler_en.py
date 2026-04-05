import json
import os
import subprocess
from typing import List, Dict

from subtitle_generator import generate_documentary_subs_en

COLOR_GRADES = {
    "mystery": "eq=brightness=-0.07:contrast=1.18:saturation=0.65,vignette=PI/5,noise=alls=7:allf=t+u",
    "paranormal": "eq=brightness=-0.09:contrast=1.22:saturation=0.50,vignette=PI/4,noise=alls=11:allf=t+u",
    "historical_enigma": "eq=brightness=-0.05:contrast=1.12:saturation=0.58,vignette=PI/6",
}


def _run_and_require_output(cmd: List[str], expected_output: str):
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if not os.path.exists(expected_output) or os.path.getsize(expected_output) == 0:
        ffmpeg_error = (proc.stderr or proc.stdout or "").strip()
        if len(ffmpeg_error) > 1200:
            ffmpeg_error = ffmpeg_error[-1200:]
        raise RuntimeError(
            f"FFmpeg step failed, output not generated: {expected_output}\n"
            f"Command: {' '.join(cmd)}\n"
            f"FFmpeg output: {ffmpeg_error}"
        )


def _ass_filter_path(path: str) -> str:
    # Prefer relative forward-slash paths to avoid Windows drive-letter parsing issues in ass filter.
    p = os.path.relpath(path, start=os.getcwd()).replace("\\", "/")
    return p


def _probe_duration(audio_path: str) -> float:
    p = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", audio_path
    ], capture_output=True, text=True)
    try:
        return float((json.loads(p.stdout) or {}).get("format", {}).get("duration", 0.0))
    except Exception:
        return 0.0


def _concat_clips(clips: List[str], out_path: str):
    list_file = os.path.join(os.path.dirname(out_path), "concat_list_video.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{os.path.abspath(c)}'\n")
    _run_and_require_output([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
        "-c:v", "libx264", "-preset", "fast", "-crf", "22", "-an", out_path,
    ], out_path)


def _process_video_clip(input_path: str, output_path: str, duration: float):
    _run_and_require_output([
        "ffmpeg", "-y", "-i", input_path, "-t", str(duration),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "22", output_path,
    ], output_path)


def _image_to_ken_burns(input_path: str, output_path: str, duration: float):
    frames = max(40, int(duration * 30))
    zoom = f"zoompan=z='min(zoom+0.0006,1.12)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920"
    _run_and_require_output([
        "ffmpeg", "-y", "-loop", "1", "-i", input_path, "-t", str(duration),
        "-vf", f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,{zoom}",
        "-r", "30", "-an", "-c:v", "libx264", "-preset", "fast", output_path,
    ], output_path)


def _build_audio_mix(narration: str, music: str, duration: float, out_path: str):
    if music and os.path.exists(music):
        filter_complex = f"[1:a]volume=0.15,aloop=loop=-1:size=2e+09,atrim=duration={duration:.2f}[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[mix]"
        _run_and_require_output([
            "ffmpeg", "-y", "-i", narration, "-i", music,
            "-filter_complex", filter_complex,
            "-map", "[mix]", "-ac", "2", "-ar", "44100", "-c:a", "aac", out_path,
        ], out_path)
    else:
        _run_and_require_output([
            "ffmpeg", "-y", "-i", narration, "-c:a", "aac", out_path,
        ], out_path)


def assemble_mystery_video(
    footage_clips: List[Dict[str, str]],
    ai_images: List[str],
    narration_path: str,
    music_path: str,
    output_path: str,
    category: str = "mystery",
) -> str:
    temp_dir = os.path.dirname(output_path)
    os.makedirs(temp_dir, exist_ok=True)

    duration = max(8.0, _probe_duration(narration_path))
    sources = [c for c in footage_clips if c.get("path")]
    for img in ai_images:
        sources.append({"path": img, "type": "image"})

    if not sources:
        raise RuntimeError("No visual sources available")

    per_clip = max(1.5, duration / max(1, len(sources)))
    processed = []

    for i, src in enumerate(sources):
        out = os.path.join(temp_dir, f"proc_{i:02d}.mp4")
        src_type = src.get("type", "video")
        if src_type == "image" or str(src.get("path", "")).lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            _image_to_ken_burns(src["path"], out, per_clip)
        else:
            _process_video_clip(src["path"], out, per_clip)
        processed.append(out)

    concat_video = os.path.join(temp_dir, "concat_raw.mp4")
    _concat_clips(processed, concat_video)

    mixed_audio = os.path.join(temp_dir, "audio_mix.aac")
    _build_audio_mix(narration_path, music_path, duration, mixed_audio)

    no_subs = os.path.join(temp_dir, "no_subs.mp4")
    _run_and_require_output([
        "ffmpeg", "-y", "-i", concat_video, "-i", mixed_audio,
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-t", str(duration),
        "-movflags", "+faststart", no_subs,
    ], no_subs)

    subs = os.path.join(temp_dir, "subs.ass")
    generate_documentary_subs_en(narration_path, subs)

    with_subs = os.path.join(temp_dir, "with_subs.mp4")
    subs_filter_path = _ass_filter_path(subs)
    _run_and_require_output([
        "ffmpeg", "-y", "-i", no_subs, "-vf", f"ass={subs_filter_path}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "copy", with_subs,
    ], with_subs)

    grade = COLOR_GRADES.get(category, COLOR_GRADES["mystery"])
    _run_and_require_output([
        "ffmpeg", "-y", "-i", with_subs, "-vf", grade,
        "-c:v", "libx264", "-crf", "18", "-c:a", "copy", output_path,
    ], output_path)

    return output_path
