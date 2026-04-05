import os
import math
import shutil
import subprocess
from pathlib import Path

from viral_video_system.modules.module3_motor_b.tts_generator import tts_edge
from viral_video_system.modules.module3_motor_b.visual_generator import generate_background_images, generate_background_media
from viral_video_system.modules.module3_motor_b.music_mixer import get_royalty_free_music
from viral_video_system.modules.module3_motor_b.depth_parallax import create_parallax_clip


def _run(cmd):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except Exception:
        return False


def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def _audio_duration_seconds(audio_path):
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        audio_path,
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode("utf-8", errors="ignore").strip()
        return max(1.0, float(out))
    except Exception:
        return 45.0


def _write_fallback_srt(text, srt_path):
    words = [w for w in text.replace("\n", " ").split(" ") if w]
    if not words:
        words = ["SIN", "CONTENIDO"]
    chunk_size = 2
    t = 0.0
    lines = []
    idx = 1
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size]).upper()
        start = t
        end = t + 0.9
        lines.append(f"{idx}\n{_ts(start)} --> {_ts(end)}\n{chunk}\n")
        idx += 1
        t = end
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _ts(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def _generate_srt_with_whisper(audio_path, text_fallback, srt_path):
    try:
        import whisper

        model_name = "base"
        model = whisper.load_model(model_name)
        result = model.transcribe(audio_path, word_timestamps=True)
        lines = []
        idx = 1
        for seg in result.get("segments", []):
            words = seg.get("words", [])
            if not words:
                continue
            for i in range(0, len(words), 2):
                chunk = words[i:i + 2]
                chunk_text = " ".join((w.get("word") or "").strip() for w in chunk).upper().strip()
                if not chunk_text:
                    continue
                start = float(chunk[0].get("start", 0.0))
                end = float(chunk[-1].get("end", start + 0.8))
                lines.append(f"{idx}\n{_ts(start)} --> {_ts(end)}\n{chunk_text}\n")
                idx += 1

        if not lines:
            _write_fallback_srt(text_fallback, srt_path)
            return srt_path

        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return srt_path
    except Exception:
        _write_fallback_srt(text_fallback, srt_path)
        return srt_path


def _ass_ts(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _generate_ass_pop_subtitles(audio_path, text_fallback, ass_path):
    words = []
    try:
        import whisperx

        device = "cpu"
        audio = whisperx.load_audio(audio_path)
        model = whisperx.load_model("small", device, compute_type="int8")
        transcribed = model.transcribe(audio, batch_size=16)
        align_model, align_meta = whisperx.load_align_model(language_code=transcribed["language"], device=device)
        aligned = whisperx.align(transcribed["segments"], align_model, align_meta, audio, device, return_char_alignments=False)
        for seg in aligned.get("segments", []):
            for w in seg.get("words", []):
                if "start" in w and "end" in w:
                    words.append((str(w.get("word", "")).strip(), float(w["start"]), float(w["end"])))
    except Exception:
        try:
            import whisper

            model = whisper.load_model("base")
            result = model.transcribe(audio_path, word_timestamps=True)
            for seg in result.get("segments", []):
                for w in seg.get("words", []):
                    words.append((str(w.get("word", "")).strip(), float(w.get("start", 0)), float(w.get("end", 0))))
        except Exception:
            pass

    if not words:
        _write_fallback_srt(text_fallback, ass_path.replace(".ass", ".srt"))
        return ""

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Base,Arial Black,92,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,2,2,40,40,520,1
Style: Pop,Arial Black,98,&H0000E5FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,8,2,2,40,40,520,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]

    for i in range(0, len(words), 3):
        chunk = words[i:i + 3]
        start = chunk[0][1]
        end = chunk[-1][2]
        base_text = " ".join(w[0].upper() for w in chunk if w[0])
        lines.append(f"Dialogue: 0,{_ass_ts(start)},{_ass_ts(end)},Base,,0,0,0,,{base_text}")
        for w_text, w_start, w_end in chunk:
            if not w_text:
                continue
            dur_ms = int(max(80, (w_end - w_start) * 1000))
            pop = min(120, int(dur_ms * 0.5))
            anim = f"{{\\c&H0000E5FF&\\bord8\\t(0,{pop},\\fscx120\\fscy120)\\t({pop},{dur_ms},\\fscx100\\fscy100)}}"
            lines.append(f"Dialogue: 1,{_ass_ts(w_start)},{_ass_ts(w_end)},Pop,,0,0,0,,{anim}{w_text.upper()}")

    with open(ass_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return ass_path


def _ensure_music(temp_dir, duration_seconds, dry_run):
    music = get_royalty_free_music(mood="motivational", duration_needed=int(duration_seconds), dry_run=dry_run)
    if music and os.path.exists(music):
        return music

    # Fallback: generate synthetic background tone locally with ffmpeg
    fallback_music = os.path.join(temp_dir, "music_fondo_fallback.mp3")
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=220:duration={max(30, int(duration_seconds))}",
        "-q:a",
        "4",
        fallback_music,
    ]
    if _run(cmd) and os.path.exists(fallback_music):
        return fallback_music

    return ""


def _assemble_part_video(media_assets, audio_path, out_video_path, dark_opacity=0.35):
    duration = _audio_duration_seconds(audio_path)
    asset_count = max(1, len(media_assets))
    per_img = max(1.0, duration / asset_count)
    zoom_frames = max(40, int(math.ceil(per_img * 25)))

    cmd = ["ffmpeg", "-y"]
    for asset in media_assets:
        path = asset.get("path")
        kind = asset.get("type", "image")
        if kind == "video":
            cmd.extend(["-stream_loop", "-1", "-t", f"{per_img:.3f}", "-i", path])
        else:
            cmd.extend(["-loop", "1", "-t", f"{per_img:.3f}", "-i", path])
    cmd.extend(["-i", audio_path])

    filters = []
    for i in range(asset_count):
        filters.append(
            f"[{i}:v]fps=30,scale=1080:1920,zoompan=z='min(zoom+0.0012,1.08)':d={zoom_frames}:s=1080x1920,eq=saturation=1.25:contrast=1.07[v{i}]"
        )
    concat_inputs = "".join([f"[v{i}]" for i in range(asset_count)])
    filters.append(f"{concat_inputs}concat=n={asset_count}:v=1:a=0[vcat]")
    filters.append(f"[vcat]unsharp=5:5:0.9:3:3:0.2,eq=gamma=1.03,drawbox=x=0:y=0:w=iw:h=ih:color=black@{dark_opacity}:t=fill[vout]")
    filter_complex = ";".join(filters)

    cmd.extend([
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-map",
        f"{asset_count}:a",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        out_video_path,
    ])

    return _run(cmd)


def _burn_subtitles(input_video, srt_path, out_video):
    subtitle_filter = "subtitles=" + srt_path
    if str(srt_path).lower().endswith(".ass"):
        subtitle_filter = "ass=" + srt_path

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_video,
        "-vf",
        subtitle_filter + ("" if str(srt_path).lower().endswith(".ass") else ":force_style='FontName=Arial,FontSize=22,Bold=1,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=3,MarginV=180'"),
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-c:a",
        "copy",
        out_video,
    ]
    return _run(cmd)


def _mix_background_music(input_video, music_path, out_video):
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        input_video,
        "-i",
        music_path,
        "-filter_complex",
        "[1:a]volume=0.18[music];[0:a][music]amix=inputs=2:duration=first:normalize=0[aout]",
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        out_video,
    ]
    return _run(cmd)


def _concat_parts(part_videos, output_path):
    list_path = os.path.join(os.path.dirname(output_path), "lista.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for path in part_videos:
            f.write(f"file '{path}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        list_path,
        "-c",
        "copy",
        output_path,
    ]
    return _run(cmd), list_path


def build_motor_b_video_suite(script, keywords, out_dir, temp_dir, dry_run=False, language="es", style_profile="default"):
    _ensure_dir(out_dir)
    _ensure_dir(temp_dir)

    parts = [
        (1, (script or {}).get("parte_1", "")),
        (2, (script or {}).get("parte_2", "")),
        (3, (script or {}).get("parte_3", "")),
    ]

    generated_parts = []
    for idx, part_text in parts:
        part_dir = os.path.join(temp_dir, f"parte_{idx}")
        _ensure_dir(part_dir)

        audio_path = os.path.join(part_dir, f"parte_{idx}.mp3")
        if language == "en":
            audio_path = tts_edge(part_text or f"Part {idx}", audio_path, voice="en-US-GuyNeural", rate="-8%", pitch="-8Hz")
        else:
            audio_path = tts_edge(part_text or f"Parte {idx}", audio_path, voice="es-ES-AlvaroNeural", rate="-8%", pitch="-10Hz")

        # If TTS fallback produced text file, keep a stable audio fallback via ffmpeg silence.
        if not str(audio_path).lower().endswith(".mp3"):
            silent_audio = os.path.join(part_dir, f"parte_{idx}.mp3")
            _run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "50", "-q:a", "9", silent_audio
            ])
            if os.path.exists(silent_audio):
                audio_path = silent_audio

        media_assets = generate_background_media(
            keywords=keywords,
            output_dir=part_dir,
            num_assets=6,
            dry_run=dry_run,
            style_profile=style_profile,
        )

        if not media_assets:
            images = generate_background_images(
                keywords=keywords,
                output_dir=part_dir,
                num_images=4,
                style="cinematic",
                dry_run=dry_run,
            )
            images = [img for img in images if str(img).lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
            media_assets = [{"type": "image", "path": img} for img in images]

        if not media_assets:
            img_fallback = os.path.join(part_dir, "bg_0.jpg")
            _run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=1", "-frames:v", "1", img_fallback
            ])
            if os.path.exists(img_fallback):
                media_assets = [{"type": "image", "path": img_fallback}]

        # Upgrade static images to depth-parallax clips when possible.
        parallax_assets = []
        for a_idx, asset in enumerate(media_assets):
            if asset.get("type") != "image":
                parallax_assets.append(asset)
                continue
            src_img = asset.get("path")
            if not src_img or not os.path.exists(src_img):
                continue

            parallax_out = os.path.join(part_dir, f"parallax_{idx}_{a_idx}.mp4")
            parallax = create_parallax_clip(
                image_path=src_img,
                output_path=parallax_out,
                duration=6.0,
                fps=30,
                width=1080,
                height=1920,
            )
            if parallax and os.path.exists(parallax):
                parallax_assets.append({"type": "video", "path": parallax})
            else:
                parallax_assets.append(asset)

        media_assets = parallax_assets or media_assets

        part_video_raw = os.path.join(out_dir, f"parte_{idx}_video.mp4")
        dark_opacity = 0.55 if style_profile == "mystery" else 0.35
        built = _assemble_part_video(media_assets, audio_path, part_video_raw, dark_opacity=dark_opacity)
        if not built:
            # Last-resort fallback video to keep pipeline running
            _run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1080x1920:d=50", "-i", audio_path,
                "-shortest", "-c:v", "libx264", "-c:a", "aac", part_video_raw
            ])

        subtitle_path = os.path.join(part_dir, f"parte_{idx}.ass")
        subtitle_generated = _generate_ass_pop_subtitles(audio_path, part_text, subtitle_path)
        if not subtitle_generated:
            subtitle_path = os.path.join(part_dir, f"parte_{idx}.srt")
            _generate_srt_with_whisper(audio_path, part_text, subtitle_path)

        part_video_subbed = os.path.join(out_dir, f"parte_{idx}_final.mp4")
        if not _burn_subtitles(part_video_raw, subtitle_path, part_video_subbed):
            shutil.copy2(part_video_raw, part_video_subbed)

        duration = _audio_duration_seconds(audio_path)
        music_path = _ensure_music(part_dir, duration, dry_run=dry_run)
        part_video_music = os.path.join(out_dir, f"parte_{idx}_con_musica.mp4")
        if music_path and os.path.exists(music_path):
            if not _mix_background_music(part_video_subbed, music_path, part_video_music):
                shutil.copy2(part_video_subbed, part_video_music)
        else:
            shutil.copy2(part_video_subbed, part_video_music)

        generated_parts.append({
            "part": idx,
            "text": part_text,
            "audio": audio_path,
            "images": [m.get("path") for m in media_assets],
            "video_raw": part_video_raw,
            "subtitles": subtitle_path,
            "video_subbed": part_video_subbed,
            "video_music": part_video_music,
        })

    final_video = os.path.join(out_dir, "video_final_completo.mp4")
    concat_ok, list_path = _concat_parts([p["video_music"] for p in generated_parts], final_video)
    if not concat_ok:
        # fallback: first part only
        shutil.copy2(generated_parts[0]["video_music"], final_video)

    return {
        "parts": generated_parts,
        "video_final_completo": final_video,
        "concat_list": list_path,
    }


def build_motor_b_dual_mystery_suite(script_by_lang, keywords, out_dir, temp_dir, dry_run=False):
    os.makedirs(out_dir, exist_ok=True)
    outputs = {}
    for lang in ["es", "en"]:
        lang_out = os.path.join(out_dir, lang)
        lang_temp = os.path.join(temp_dir, lang)
        suite = build_motor_b_video_suite(
            script=script_by_lang.get(lang) or {},
            keywords=keywords,
            out_dir=lang_out,
            temp_dir=lang_temp,
            dry_run=dry_run,
            language=lang,
            style_profile="mystery",
        )
        outputs[lang] = suite

    return {
        "channels": outputs,
        "video_final_completo": (outputs.get("es") or {}).get("video_final_completo", ""),
        "concat_list": (outputs.get("es") or {}).get("concat_list", ""),
        "parts": (outputs.get("es") or {}).get("parts", []),
    }
