"""
YouTube Automation Pro — Video Builder
Professional video assembly with B-roll, subtitles, color grading,
Ken Burns effects, intro/outro, and background music.
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import requests

from ..config import env, env_int, CHANNEL_DIRS, ASSETS_DIR
from ..database import log_api_usage, log_pipeline_step, update_video
from .runtime import QuotaManager, FallbackChain

logger = logging.getLogger("video-builder")
QUOTA = QuotaManager()

# ── Color grading presets per channel ────────────────────────
COLOR_GRADING = {
    "impacto-mundial": "eq=contrast=1.15:saturation=0.9:brightness=-0.02,colortemperature=6800,vignette=PI/4",
    "mentes-rotas": "eq=contrast=1.12:saturation=0.8:brightness=-0.03,colortemperature=7500,vignette=PI/3.5",
    "el-loco-de-la-ia": "eq=contrast=1.10:saturation=1.15:brightness=0.01,colortemperature=6200",
    "mind-warp": "eq=contrast=1.12:saturation=0.95:brightness=-0.01,colortemperature=6500,vignette=PI/5",
    "wealth-files": "eq=contrast=1.08:saturation=1.05:brightness=0.02,colortemperature=5500",
    "dark-science": "eq=contrast=1.20:saturation=0.85:brightness=-0.03,colortemperature=8000,vignette=PI/3",
}

# ── Subtitle styles per channel ──────────────────────────────
SUBTITLE_COLORS = {
    "impacto-mundial": {"text": "#FFFFFF", "outline": "#000000", "highlight": "#C8A829"},
    "mentes-rotas": {"text": "#FFFFFF", "outline": "#000000", "highlight": "#DC143C"},
    "el-loco-de-la-ia": {"text": "#FFFFFF", "outline": "#000000", "highlight": "#00E5FF"},
    "mind-warp": {"text": "#FFFFFF", "outline": "#000000", "highlight": "#7B1FA2"},
    "wealth-files": {"text": "#FFFFFF", "outline": "#000000", "highlight": "#FFD700"},
    "dark-science": {"text": "#FFFFFF", "outline": "#000000", "highlight": "#1565C0"},
}

REMOTION_INTRO_COMPONENTS = {
    "impacto-mundial": "ImpactoMundialIntro",
    "mentes-rotas": "MentesRotasIntro",
    "el-loco-de-la-ia": "LocoIAIntro",
    "mind-warp": "MindWarpIntro",
    "wealth-files": "WealthFilesIntro",
    "dark-science": "DarkScienceIntro",
}

CHANNEL_BROLL_FALLBACKS = {
    "impacto-mundial": ["declassified files", "underground bunker", "world map surveillance"],
    "mentes-rotas": ["crime investigation board", "forensic lab", "night police lights"],
    "el-loco-de-la-ia": ["ai dashboard screen", "coding workstation", "robotics laboratory"],
    "mind-warp": ["brain activity animation", "psychology experiment", "people in crowd slow motion"],
    "wealth-files": ["financial charts growth", "city skyline luxury", "corporate meeting"],
    "dark-science": ["deep space stars", "particle collider", "deep ocean exploration"],
}


# ═══════════════════════════════════════════════════════════════
# B-Roll Downloading
# ═══════════════════════════════════════════════════════════════


def _normalize_query(query: str) -> str:
    query = re.sub(r"\s+", " ", query.strip().lower())
    query = re.sub(r"[^a-z0-9À-ÿ\s-]", "", query)
    return query[:80]


def _extract_context_keywords(text: str, limit: int = 10) -> list[str]:
    """Extract meaningful context keywords to improve footage relevance."""
    stop = {
        "de", "la", "el", "los", "las", "un", "una", "y", "o", "que", "en", "del", "al",
        "por", "para", "con", "sobre", "lo", "se", "su", "sus", "como", "más", "menos",
        "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "about",
        "from", "is", "are", "was", "were", "be", "this", "that", "these", "those",
    }
    words = re.findall(r"[a-zA-ZÀ-ÿ0-9]{4,}", text.lower())
    out: list[str] = []
    for w in words:
        if w in stop or w in out:
            continue
        out.append(w)
        if len(out) >= limit:
            break
    return out


def _pexels_search(query: str, per_page: int = 5) -> list[str]:
    """Search Pexels for stock video clips."""
    key = env("PEXELS_API_KEY")
    if not key:
        return []
    if not QUOTA.allow("pexels", cost=1):
        logger.warning("Pexels quota reached. Skipping query '%s'.", query)
        return []
    try:
        resp = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": key},
            params={"query": query, "per_page": per_page, "orientation": "landscape", "min_duration": 5},
            timeout=30,
        )
        if resp.status_code != 200:
            return []
        urls = []
        for v in resp.json().get("videos", []):
            files = v.get("video_files", [])
            mp4 = [f for f in files if "video/mp4" in f.get("file_type", "")]
            if mp4:
                # Prefer HD
                hd = [f for f in mp4 if f.get("width", 0) >= 1280]
                selected = (hd or mp4)[0]
                if selected.get("link"):
                    urls.append(selected["link"])
        log_api_usage("pexels", "videos/search", requests=1)
        return urls
    except Exception as exc:
        logger.warning(f"Pexels error: {exc}")
        return []


def _pixabay_search(query: str, per_page: int = 5) -> list[str]:
    """Search Pixabay for stock video clips."""
    key = env("PIXABAY_API_KEY")
    if not key:
        return []
    if not QUOTA.allow("pixabay", cost=1):
        logger.warning("Pixabay quota reached. Skipping query '%s'.", query)
        return []
    try:
        resp = requests.get(
            "https://pixabay.com/api/videos/",
            params={"key": key, "q": query, "per_page": per_page},
            timeout=30,
        )
        if resp.status_code != 200:
            return []
        urls = []
        for hit in resp.json().get("hits", []):
            videos = hit.get("videos", {})
            url = (videos.get("large", {}).get("url")
                   or videos.get("medium", {}).get("url")
                   or videos.get("small", {}).get("url"))
            if url:
                urls.append(url)
        log_api_usage("pixabay", "videos", requests=1)
        return urls
    except Exception as exc:
        logger.warning(f"Pixabay error: {exc}")
        return []


def _download_clip(url: str, output: Path) -> bool:
    """Download a video clip."""
    try:
        resp = requests.get(url, timeout=120, stream=True)
        if resp.status_code != 200:
            return False
        with open(output, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        return output.exists() and output.stat().st_size > 50_000
    except Exception:
        return False


def _file_fingerprint(path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Create a compact fingerprint to detect duplicate media files."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read(chunk_size))
    return h.hexdigest()


def _load_usage_ledger(clips_dir: Path) -> dict:
    ledger_path = clips_dir / "_asset_usage.json"
    if not ledger_path.exists():
        return {"used_urls": [], "used_hashes": []}
    try:
        return json.loads(ledger_path.read_text(encoding="utf-8"))
    except Exception:
        return {"used_urls": [], "used_hashes": []}


def _save_usage_ledger(clips_dir: Path, ledger: dict) -> None:
    ledger_path = clips_dir / "_asset_usage.json"
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")


def _wikimedia_search_images(query: str, limit: int = 6) -> list[str]:
    """Search Wikimedia Commons images (free, no API key)."""
    try:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {query}",
            "gsrlimit": max(1, min(limit, 20)),
            "gsrnamespace": 6,  # File namespace
            "prop": "imageinfo",
            "iiprop": "url",
        }
        resp = requests.get(
            "https://commons.wikimedia.org/w/api.php",
            params=params,
            timeout=20,
            headers={"User-Agent": "youtube-automation-pro/2.0"},
        )
        if resp.status_code != 200:
            return []
        pages = (resp.json().get("query", {}) or {}).get("pages", {}) or {}
        urls: list[str] = []
        for page in pages.values():
            for info in page.get("imageinfo", []) or []:
                url = info.get("url", "")
                if isinstance(url, str) and url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    urls.append(url)
        return urls
    except Exception as exc:
        logger.warning("Wikimedia search error for '%s': %s", query, exc)
        return []


def _download_image(url: str, output: Path) -> bool:
    """Download an image file."""
    try:
        resp = requests.get(url, timeout=60, stream=True, headers={"User-Agent": "youtube-automation-pro/2.0"})
        if resp.status_code != 200:
            return False
        with open(output, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return output.exists() and output.stat().st_size > 25_000
    except Exception:
        return False


def _image_to_clip(image_path: Path, output_path: Path, channel_id: str, seconds: float = 5.0) -> bool:
    """Convert still image into a cinematic motion clip."""
    grading = COLOR_GRADING.get(channel_id, "eq=contrast=1.1:saturation=1.0")
    frames = max(90, int(seconds * 30))
    vf = (
        "scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080,"
        f"zoompan=z='min(zoom+0.0012,1.12)':d={frames}:s=1920x1080,"
        "fps=30,"
        f"{grading}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-t", f"{seconds:.2f}",
        "-vf", vf,
        "-an",
        "-c:v", "libx264", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        return result.returncode == 0 and output_path.exists() and _probe_duration(output_path) >= 3.0
    except Exception:
        return False


def download_broll(
    broll_markers: list[str],
    channel: dict,
    min_clips: int = 10,
    topic: str = "",
    script_text: str = "",
) -> list[Path]:
    """Download B-roll clips based on script markers."""
    channel_id = channel["channel_id"]
    channel_dir = CHANNEL_DIRS.get(channel_id)
    if not channel_dir:
        return []

    clips_dir = channel_dir / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    ledger = _load_usage_ledger(clips_dir)
    used_urls = set(ledger.get("used_urls", []))
    used_hashes = set(ledger.get("used_hashes", []))

    # Combine script markers with topic/script context and channel fallback queries
    channel_fallback = CHANNEL_BROLL_FALLBACKS.get(channel_id, [])
    context_keywords = _extract_context_keywords(f"{topic} {script_text}", limit=8)
    semantic_queries = []
    if topic:
        semantic_queries.extend([
            f"{topic} documentary",
            f"{topic} archive footage",
            f"{topic} cinematic broll",
        ])
    semantic_queries.extend([f"{k} documentary footage" for k in context_keywords[:5]])
    fallback_queries = channel_fallback + [
        "cinematic aerial landscape",
        "dramatic close up face",
        "timelapse city lights night",
    ]
    raw_queries = list(broll_markers[:14]) + semantic_queries + fallback_queries
    queries: list[str] = []
    for q in raw_queries:
        nq = _normalize_query(q)
        if nq and nq not in queries:
            queries.append(nq)

    all_urls: list[str] = []
    for query in queries:
        if len(all_urls) >= min_clips * 2:
            break
        chain = (
            FallbackChain("broll-provider")
            .add("pexels", lambda q=query: _pexels_search(q, per_page=3))
            .add("pixabay", lambda q=query: _pixabay_search(q, per_page=3))
        )
        _, provider_urls = chain.run()
        if provider_urls:
            for u in provider_urls:
                if u in used_urls or u in all_urls:
                    continue
                all_urls.append(u)

    # Download clips
    downloaded: list[Path] = []
    for idx, url in enumerate(all_urls, start=1):
        if len(downloaded) >= min_clips:
            break
        out = clips_dir / f"broll_{idx:03d}.mp4"
        if _download_clip(url, out):
            try:
                fp = _file_fingerprint(out)
                if fp in used_hashes:
                    out.unlink(missing_ok=True)
                    continue
            except Exception:
                fp = ""
            # Verify duration
            dur = _probe_duration(out)
            if dur >= 3.0:
                downloaded.append(out)
                logger.info(f"   Downloaded clip {idx}: {dur:.1f}s")
                used_urls.add(url)
                if fp:
                    used_hashes.add(fp)
            else:
                out.unlink(missing_ok=True)

    logger.info(f"   📹 Downloaded {len(downloaded)} B-roll clips")

    # Free fallback: create motion clips from Wikimedia Commons images
    if len(downloaded) < min_clips:
        needed = min_clips - len(downloaded)
        logger.info("   Need %s more clips. Trying Wikimedia image fallback...", needed)
        image_queries = queries[:8] or ["documentary", "history", "city", "technology"]
        image_urls: list[str] = []
        for q in image_queries:
            if len(image_urls) >= needed * 3:
                break
            image_urls.extend(_wikimedia_search_images(q, limit=4))

        # de-duplicate URLs while preserving order
        seen_urls: set[str] = set()
        unique_urls: list[str] = []
        for u in image_urls:
            if u not in seen_urls:
                seen_urls.add(u)
                unique_urls.append(u)

        fallback_added = 0
        for idx, url in enumerate(unique_urls, start=1):
            if len(downloaded) >= min_clips:
                break
            if url in used_urls:
                continue
            img_path = clips_dir / f"broll_img_{idx:03d}.jpg"
            clip_path = clips_dir / f"broll_img_{idx:03d}.mp4"
            if not _download_image(url, img_path):
                continue
            if _image_to_clip(img_path, clip_path, channel_id, seconds=5.5):
                try:
                    fp = _file_fingerprint(clip_path)
                    if fp in used_hashes:
                        clip_path.unlink(missing_ok=True)
                        img_path.unlink(missing_ok=True)
                        continue
                    used_hashes.add(fp)
                except Exception:
                    pass
                downloaded.append(clip_path)
                fallback_added += 1
                used_urls.add(url)
            img_path.unlink(missing_ok=True)
        if fallback_added:
            logger.info("   Added %s fallback clips from Wikimedia images", fallback_added)

    ledger["used_urls"] = list(used_urls)[-1200:]
    ledger["used_hashes"] = list(used_hashes)[-1200:]
    _save_usage_ledger(clips_dir, ledger)

    return downloaded


# ═══════════════════════════════════════════════════════════════
# Video Assembly
# ═══════════════════════════════════════════════════════════════

def _probe_duration(path: Path) -> float:
    """Get media file duration in seconds."""
    try:
        cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "json", str(path)]
        raw = subprocess.check_output(cmd, text=True, timeout=30)
        return float(json.loads(raw)["format"]["duration"])
    except Exception:
        return 0.0


def _normalize_clip(input_path: Path, output_path: Path, channel_id: str) -> bool:
    """Normalize a clip to 1920x1080, 30fps with color grading."""
    grading = COLOR_GRADING.get(channel_id, "eq=contrast=1.1:saturation=1.0")
    is_generated_fallback = input_path.stem.startswith("broll_img_")
    if is_generated_fallback:
        vf = (
            "scale=1920:1080:force_original_aspect_ratio=increase,"
            "crop=1920:1080,"
            "fps=30,"
            f"{grading}"
        )
        timeout = 60
    else:
        # Modern "Spectacular" Effects Pipeline
        vf = (
            "scale=1920:1080:force_original_aspect_ratio=increase,"
            "crop=1920:1080,"
            "fps=30,"
            "setpts=1.05*PTS,"
            f"{grading},"
            "unsharp=5:5:0.8:5:5:0.0" # Sharpen for crispness
        )
        timeout = 120

    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", vf,
        "-an",  # No audio from clips
        "-c:v", "libx264", "-preset", "fast",
        "-b:v", "12M", "-maxrate", "15M", "-bufsize", "24M", # Higher bitrate for spectacular look
        "-pix_fmt", "yuv420p",
        str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return result.returncode == 0 and output_path.exists()
    except Exception as exc:
        logger.warning(f"Clip normalize error: {exc}")
        return False


def _build_video_track(clips: list[Path], audio_duration: float,
                       channel_id: str, temp_dir: Path) -> Path:
    """Build the video track from B-roll clips, looping as needed."""
    norm_dir = temp_dir / "normalized"
    norm_dir.mkdir(exist_ok=True)

    # Normalize all clips
    normalized: list[Path] = []
    for idx, clip in enumerate(clips, start=1):
        out = norm_dir / f"norm_{idx:03d}.mp4"
        if _normalize_clip(clip, out, channel_id):
            normalized.append(out)

    if not normalized:
        raise RuntimeError("No clips could be normalized")

    # Prepare paced shots so cuts are not too fast.
    target_shot = {
        "impacto-mundial": 6.8,
        "mentes-rotas": 6.6,
        "el-loco-de-la-ia": 5.5,
        "mind-warp": 6.2,
        "wealth-files": 6.0,
        "dark-science": 7.0,
    }.get(channel_id, 6.2)

    paced_dir = temp_dir / "paced"
    paced_dir.mkdir(exist_ok=True)
    paced: list[Path] = []
    for idx, clip in enumerate(normalized, start=1):
        out = paced_dir / f"shot_{idx:03d}.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", str(clip),
            "-t", f"{target_shot:.2f}",
            "-vf", "setpts=1.03*PTS",
            "-an",
            "-c:v", "libx264", "-preset", "veryfast",
            "-pix_fmt", "yuv420p",
            str(out),
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=180)
            if result.returncode == 0 and out.exists() and _probe_duration(out) >= max(4.8, target_shot - 1):
                paced.append(out)
        except Exception:
            continue
    if paced:
        normalized = paced

    # Build sequence to fill audio duration
    sequence: list[Path] = []
    acc = 0.0
    guard = 0
    while acc < audio_duration + 2 and guard < 500:
        for clip in normalized:
            sequence.append(clip)
            acc += max(0.1, _probe_duration(clip))
            if acc >= audio_duration + 2:
                break
        guard += 1

    # Concat all
    list_file = temp_dir / "concat_list.txt"
    lines = [f"file '{clip.as_posix()}'" for clip in sequence]
    list_file.write_text("\n".join(lines), encoding="utf-8")

    merged = temp_dir / "video_track.mp4"
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
           "-i", str(list_file), "-c", "copy", str(merged)]
    subprocess.run(cmd, capture_output=True, check=True, timeout=300)

    return merged


def _build_thumbnail_video(thumbnail_path: Path, audio_duration: float,
                           temp_dir: Path) -> Path:
    """Create video from static thumbnail with Ken Burns zoom effect."""
    out = temp_dir / "video_track.mp4"
    # Slow zoom from 1.0 to 1.08
    duration = max(5, int(audio_duration + 2))
    cmd = [
        "ffmpeg", "-y", "-loop", "1",
        "-i", str(thumbnail_path),
        "-t", str(duration),
        "-vf", "scale=1920:1080,fps=30,zoompan=z='min(zoom+0.0009,1.08)':d=125:s=1920x1080",
        "-c:v", "libx264", "-b:v", "8M", "-pix_fmt", "yuv420p",
        str(out),
    ]
    subprocess.run(cmd, capture_output=True, check=True, timeout=600)
    return out


def _generate_subtitles(script_text: str, audio_duration: float,
                        channel_id: str, temp_dir: Path) -> Path | None:
    """Generate readable SRT subtitles from script text with timing estimates."""
    clean = re.sub(r'\[B-ROLL:.*?\]', '', script_text)
    clean = re.sub(r'^##.*$', '', clean, flags=re.MULTILINE)
    # Remove metadata sections
    for marker in ["TITLES", "TÍTULOS", "SEO DESCRIPTION", "TAGS", "SHORT VERSION"]:
        idx = clean.upper().find(f"## {marker}")
        if idx > 0:
            clean = clean[:idx]

    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        return None

    # Prefer sentence-level chunks, then split long sentences for readability.
    raw_sentences = re.split(r'(?<=[\.\!\?])\s+', clean)
    segments: list[str] = []
    for sentence in raw_sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        words = sentence.split()
        while len(words) > 14:
            head = words[:14]
            segments.append(" ".join(head))
            words = words[14:]
        if words:
            segments.append(" ".join(words))

    words = clean.split()
    if not segments:
        return None

    # Calculate timing
    total_words = len(words)
    time_per_word = audio_duration / max(1, total_words)

    srt_path = temp_dir / "subtitles.srt"
    srt_lines: list[str] = []
    word_pos = 0

    for idx, seg in enumerate(segments, start=1):
        seg_words = len(seg.split())
        start_time = word_pos * time_per_word
        duration = max(1.2, min(4.0, seg_words * time_per_word))
        end_time = min(audio_duration, start_time + duration)
        word_pos += seg_words

        start_str = _format_srt_time(start_time)
        end_str = _format_srt_time(end_time)

        srt_lines.append(f"{idx}")
        srt_lines.append(f"{start_str} --> {end_str}")
        srt_lines.append(seg.strip())
        srt_lines.append("")

    srt_path.write_text("\n".join(srt_lines), encoding="utf-8")
    return srt_path


def _format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT timestamp format."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _burn_subtitles(video_path: Path, srt_path: Path, channel_id: str,
                    output_path: Path) -> bool:
    """Burn subtitles into the video with channel-specific styling."""
    colors = SUBTITLE_COLORS.get(channel_id, {"text": "#FFFFFF", "outline": "#000000"})

    # Convert hex colors to ASS format (BGR)
    def hex_to_ass(hex_color: str) -> str:
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        return f"&H00{b:02X}{g:02X}{r:02X}"

    primary = hex_to_ass(colors["text"])
    outline = hex_to_ass(colors["outline"])

    back = "&H88000000"  # semi-transparent black box
    # Subtitle filter with stronger readability for mobile/short-form viewers
    sub_filter = (
        f"subtitles={srt_path.as_posix()}:"
        f"force_style='Fontname=Arial,Fontsize=22,"
        f"PrimaryColour={primary},"
        f"OutlineColour={outline},"
        f"BackColour={back},"
        f"BorderStyle=4,Outline=1.6,Shadow=0,"
        f"MarginV=46,Alignment=2'"
    )

    cmd = [
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", sub_filter,
        "-c:v", "libx264", "-preset", "veryfast",
        "-b:v", "8M", "-c:a", "copy",
        str(output_path),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=600)
        return result.returncode == 0 and output_path.exists()
    except Exception as exc:
        logger.warning(f"Subtitle burn error: {exc}")
        return False


def _render_remotion_intro(channel_id: str, temp_dir: Path) -> Path | None:
    """Render an intro clip with Remotion when available. Returns None if unavailable."""
    project_root = Path(__file__).resolve().parents[2]
    remotion_dir = project_root / "remotion"
    if not remotion_dir.exists():
        return None

    composition = REMOTION_INTRO_COMPONENTS.get(channel_id)
    if not composition:
        return None

    intro_out = temp_dir / f"{channel_id}_intro.mp4"
    local_remotion_cmd = remotion_dir / "node_modules" / ".bin" / "remotion.cmd"
    local_remotion_sh = remotion_dir / "node_modules" / ".bin" / "remotion"
    render_args = [
        "render", "src/index.tsx", composition, str(intro_out),
        "--concurrency", "1", "--cwd", str(remotion_dir),
    ]
    if local_remotion_cmd.exists():
        cmd = [str(local_remotion_cmd), *render_args]
    elif local_remotion_sh.exists():
        cmd = [str(local_remotion_sh), *render_args]
    elif shutil.which("npm"):
        cmd = ["npm", "exec", "--yes", "remotion", *render_args]
    else:
        return None

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=600, cwd=remotion_dir)
        if result.returncode == 0 and intro_out.exists():
            return intro_out
        logger.warning("Remotion intro render failed for %s: %s", channel_id, result.stderr.decode(errors="ignore")[:300])
    except Exception as exc:
        logger.warning("Remotion intro render error for %s: %s", channel_id, exc)
    return None


# ═══════════════════════════════════════════════════════════════
# Main Build Function
# ═══════════════════════════════════════════════════════════════

def build_video(audio_path: Path, script_text: str, thumbnail_path: Path,
                clips: list[Path], channel: dict,
                video_id: int | None = None) -> Path:
    """
    Build the complete video with B-roll, subtitles, and effects.
    """
    channel_id = channel["channel_id"]
    channel_dir = CHANNEL_DIRS.get(channel_id)
    timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")

    if channel_dir:
        final_output = channel_dir / "videos" / f"{timestamp}_video.mp4"
    else:
        final_output = Path(f"{timestamp}_video.mp4")

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio not found: {audio_path}")

    audio_duration = _probe_duration(audio_path)
    if audio_duration <= 0:
        raise RuntimeError("Invalid audio: 0 seconds")

    logger.info(f"🎬 Building video for '{channel['name']}' ({audio_duration:.0f}s audio)")

    with tempfile.TemporaryDirectory(prefix="ytauto_build_") as td:
        temp_dir = Path(td)

        # Step 1: Build video track
        usable_clips = [c for c in clips if c.exists()]
        if usable_clips:
            logger.info(f"   Building video from {len(usable_clips)} B-roll clips...")
            video_track = _build_video_track(usable_clips, audio_duration, channel_id, temp_dir)
        else:
            logger.info("   No B-roll clips, building from thumbnail...")
            video_track = _build_thumbnail_video(thumbnail_path, audio_duration, temp_dir)

        # Step 2: Generate subtitles
        logger.info("   Generating subtitles...")
        srt_path = _generate_subtitles(script_text, audio_duration, channel_id, temp_dir)

        # Step 3: Merge video + audio
        logger.info("   Merging video + audio...")
        merged = temp_dir / "merged.mp4"
        cmd_merge = [
            "ffmpeg", "-y",
            "-i", str(video_track),
            "-i", str(audio_path),
            "-c:v", "libx264", "-preset", "veryfast",
            "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(merged),
        ]
        subprocess.run(cmd_merge, capture_output=True, check=True, timeout=600)

        # Step 4: Burn subtitles
        if srt_path and srt_path.exists():
            logger.info("   Burning subtitles...")
            subtitled = temp_dir / "subtitled.mp4"
            if _burn_subtitles(merged, srt_path, channel_id, subtitled):
                merged = subtitled

        # Step 4.5: Optional Remotion intro prepend
        intro_clip = _render_remotion_intro(channel_id, temp_dir)
        if intro_clip:
            logger.info("   Prepending Remotion intro...")
            list_file = temp_dir / "intro_concat.txt"
            list_file.write_text(
                f"file '{intro_clip.as_posix()}'\nfile '{merged.as_posix()}'\n",
                encoding="utf-8",
            )
            intro_merged = temp_dir / "intro_merged.mp4"
            cmd_intro = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-c:v", "libx264", "-preset", "veryfast",
                "-c:a", "aac",
                str(intro_merged),
            ]
            subprocess.run(cmd_intro, capture_output=True, check=True, timeout=600)
            merged = intro_merged

        # Step 5: Final encode to output
        logger.info("   Final encoding...")
        final_output.parent.mkdir(parents=True, exist_ok=True)
        cmd_final = [
            "ffmpeg", "-y", "-i", str(merged),
            "-c:v", "libx264", "-preset", "slow",
            "-b:v", "8M", "-maxrate", "10M", "-bufsize", "16M",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "320k",
            "-movflags", "+faststart",
            str(final_output),
        ]
        subprocess.run(cmd_final, capture_output=True, check=True, timeout=900)

    # Verify output
    if not final_output.exists():
        raise RuntimeError("Video build failed: output file not created")

    final_duration = _probe_duration(final_output)
    final_size_mb = final_output.stat().st_size / (1024 * 1024)
    logger.info(f"   ✅ Video built: {final_duration:.0f}s, {final_size_mb:.0f}MB")

    # Update video record
    if video_id:
        update_video(video_id, {
            "video_path": str(final_output),
            "duration_seconds": final_duration,
            "status": "video_ready",
        })
        log_pipeline_step(channel.get("id"), video_id, "video_builder", "ok",
                          f"Video built: {final_duration:.0f}s, {final_size_mb:.0f}MB")

    return final_output
