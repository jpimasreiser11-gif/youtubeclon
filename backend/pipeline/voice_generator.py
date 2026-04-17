"""
YouTube Automation Pro — Voice Generator
Multi-tier TTS: ElevenLabs → Edge TTS → gTTS
With audio post-processing and background music mixing.
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

import requests

from ..config import env, CHANNEL_DIRS
from ..database import log_api_usage, log_pipeline_step, update_video
from .runtime import FallbackChain, QuotaManager

logger = logging.getLogger("voice-generator")
QUOTA = QuotaManager()

# ── Edge TTS voice mappings per channel ──────────────────────
EDGE_VOICES = {
    "impacto-mundial": "es-ES-AlvaroNeural",       # Deep Spanish male
    "mentes-rotas": "es-MX-DaliaNeural",            # Mexican female, serious
    "el-loco-de-la-ia": "es-ES-AlvaroNeural",       # Energetic Spanish male
    "mind-warp": "en-US-GuyNeural",                  # American male, intellectual
    "wealth-files": "en-US-GuyNeural",               # Authoritative American male
    "dark-science": "en-GB-RyanNeural",              # British male, documentary
}

EDGE_RATE = {
    "impacto-mundial": "-5%",    # Slower for mystery/drama
    "mentes-rotas": "-8%",       # Even slower for true crime
    "el-loco-de-la-ia": "+5%",   # Faster for tech/energy
    "mind-warp": "-3%",          # Slightly slow for intellect
    "wealth-files": "-2%",       # Near normal, authoritative
    "dark-science": "-5%",       # Slow for wonder/awe
}

EDGE_PITCH = {
    "impacto-mundial": "-2Hz",
    "mentes-rotas": "-3Hz",
    "el-loco-de-la-ia": "+2Hz",
    "mind-warp": "-1Hz",
    "wealth-files": "-2Hz",
    "dark-science": "-3Hz",
}

EDGE_VOLUME = {
    "impacto-mundial": "+3%",
    "mentes-rotas": "+4%",
    "el-loco-de-la-ia": "+5%",
    "mind-warp": "+3%",
    "wealth-files": "+3%",
    "dark-science": "+4%",
}


# ═══════════════════════════════════════════════════════════════
# Text Processing
# ═══════════════════════════════════════════════════════════════

def _clean_script_for_tts(script: str) -> str:
    """Remove markdown, B-roll markers, and section headers from script."""
    import re
    # Remove B-roll markers
    text = re.sub(r'\[B-ROLL:.*?\]', '', script)
    # Remove markdown headers
    text = re.sub(r'^##.*$', '', text, flags=re.MULTILINE)
    # Remove title/tag/description sections at the end
    for marker in ["## TITLES", "## TÍTULOS", "## SEO DESCRIPTION",
                    "## TAGS", "## SHORT VERSION", "## VERSIÓN SHORT"]:
        idx = text.upper().find(marker.upper())
        if idx > 0:
            text = text[:idx]
    # Remove list indices / markdown symbols
    text = re.sub(r"^\s*[-*]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s*\d+[\.\)]\s+", "", text, flags=re.MULTILINE)
    # Normalize typographic symbols and quotes to avoid spoken artifacts
    symbol_map = {
        "“": "",
        "”": "",
        '"': "",
        "'": "",
        "‘": "",
        "’": "",
        "`": "",
        "´": "",
        "—": ", ",
        "–": ", ",
        "•": " ",
        "…": "...",
    }
    for old, new in symbol_map.items():
        text = text.replace(old, new)
    # Remove markdown links and urls that sound robotic in narration
    text = re.sub(r"\[([^\]]+)\]\((https?:\/\/[^\)]+)\)", r"\1", text)
    text = re.sub(r"https?:\/\/\S+", "", text)
    text = re.sub(r"\b\w+@\w+\.\w+\b", "", text)
    # Keep punctuation clean for TTS pauses
    text = re.sub(r"[(){}\[\]<>]", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    # Improve punctuation pauses for natural TTS rhythm
    text = re.sub(r"\s*:\s*", ". ", text)
    text = re.sub(r"\s*;\s*", ". ", text)
    text = re.sub(r"\.\.\.+", "...", text)
    # Clean up whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'  +', ' ', text)
    return text.strip()


def _split_text(text: str, max_chars: int = 2200) -> list[str]:
    """Split text into chunks for TTS APIs that have character limits."""
    parts: list[str] = []
    current = ""
    for paragraph in text.split("\n"):
        p = paragraph.strip()
        if not p:
            continue
        if len(current) + len(p) + 1 <= max_chars:
            current = (current + " " + p).strip()
        else:
            if current:
                parts.append(current)
            current = p
    if current:
        parts.append(current)
    return parts or [text[:max_chars]]


# ═══════════════════════════════════════════════════════════════
# Tier 1: ElevenLabs (10K chars/month free)
# ═══════════════════════════════════════════════════════════════

def _elevenlabs_tts(text: str, out_path: Path, channel: dict) -> bool:
    """Generate audio using ElevenLabs API with channel-specific voice settings."""
    api_key = env("ELEVENLABS_API_KEY")
    if not api_key:
        return False

    voice_id = channel.get("voice_id", env("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL"))
    stability = channel.get("voice_stability", 0.45)
    similarity = channel.get("voice_similarity", 0.85)
    style = channel.get("voice_style", 0.3)

    chunks = _split_text(text, max_chars=2200)
    part_files: list[Path] = []
    temp_dir = out_path.parent

    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        }

        total_chars = 0
        for idx, chunk in enumerate(chunks, start=1):
            payload = {
                "text": chunk,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity,
                    "style": style,
                },
            }
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            if response.status_code != 200:
                logger.warning(f"ElevenLabs error: {response.status_code} — {response.text[:200]}")
                return False

            part = temp_dir / f"{out_path.stem}_el_part{idx:03d}.mp3"
            part.write_bytes(response.content)
            part_files.append(part)
            total_chars += len(chunk)

        log_api_usage("elevenlabs", "text-to-speech", chars=total_chars)

        if len(part_files) == 1:
            shutil.move(str(part_files[0]), str(out_path))
            return out_path.exists()

        return _concat_audio(part_files, out_path)
    except Exception as exc:
        logger.error(f"ElevenLabs error: {exc}")
        return False
    finally:
        for p in part_files:
            p.unlink(missing_ok=True)


# ═══════════════════════════════════════════════════════════════
# Tier 2: Edge TTS (free, unlimited, 300+ voices)
# ═══════════════════════════════════════════════════════════════

def _edge_tts(text: str, out_path: Path, channel: dict) -> bool:
    """Generate audio using Microsoft Edge TTS (free, unlimited)."""
    try:
        import edge_tts
    except ImportError:
        logger.warning("edge-tts not installed. pip install edge-tts")
        return False

    channel_id = channel.get("channel_id", "")
    voice = EDGE_VOICES.get(channel_id, "en-US-GuyNeural")
    rate = EDGE_RATE.get(channel_id, "+0%")
    pitch = EDGE_PITCH.get(channel_id, "+0Hz")
    volume = EDGE_VOLUME.get(channel_id, "+0%")

    try:
        # Edge TTS is async, run in event loop
        async def _generate():
            communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
            await communicate.save(str(out_path))

        # Run in new event loop (safe from any thread)
        loop = asyncio.new_event_loop()
        loop.run_until_complete(_generate())
        loop.close()

        if out_path.exists() and out_path.stat().st_size > 10_000:
            log_api_usage("edge_tts", "generate", chars=len(text))
            return True
        return False
    except Exception as exc:
        logger.error(f"Edge TTS error: {exc}")
        return False


# ═══════════════════════════════════════════════════════════════
# Tier 3: gTTS (free fallback, lower quality)
# ═══════════════════════════════════════════════════════════════

def _gtts_fallback(text: str, out_path: Path, language: str) -> bool:
    """Google TTS fallback — works but sounds robotic."""
    try:
        from gtts import gTTS
        lang = "es" if language.startswith("es") else "en"
        chunks = _split_text(text, max_chars=2500)
        part_files: list[Path] = []

        for idx, chunk in enumerate(chunks, start=1):
            part = out_path.parent / f"{out_path.stem}_gtts_part{idx:03d}.mp3"
            tts = gTTS(text=chunk, lang=lang, slow=False)
            tts.save(str(part))
            part_files.append(part)

        result = _concat_audio(part_files, out_path)
        for p in part_files:
            p.unlink(missing_ok=True)
        return result
    except Exception as exc:
        logger.error(f"gTTS error: {exc}")
        return False


# ═══════════════════════════════════════════════════════════════
# Audio Utilities
# ═══════════════════════════════════════════════════════════════

def _concat_audio(parts: list[Path], output: Path) -> bool:
    """Concatenate multiple audio files using FFmpeg."""
    if not parts:
        return False
    if shutil.which("ffmpeg") is None:
        logger.error("FFmpeg not found in PATH")
        return False

    with tempfile.TemporaryDirectory(prefix="ytauto_concat_") as td:
        list_file = Path(td) / "list.txt"
        lines = [f"file '{p.as_posix()}'" for p in parts]
        list_file.write_text("\n".join(lines), encoding="utf-8")
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file), "-c", "copy", str(output),
        ]
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            logger.error(f"FFmpeg concat error: {result.stderr.decode()[:300]}")
            return False

    return output.exists() and output.stat().st_size > 10_000


def _postprocess_audio(audio_path: Path) -> Path:
    """
    Post-process audio:
    - Normalize to -14 LUFS (YouTube standard)
    - Remove long silences
    - Boost mid frequencies for clarity
    """
    if shutil.which("ffmpeg") is None:
        return audio_path  # Skip if no FFmpeg

    processed = audio_path.parent / f"{audio_path.stem}_processed{audio_path.suffix}"

    cmd = [
        "ffmpeg", "-y", "-i", str(audio_path),
        "-af", (
            "silenceremove=start_periods=1:start_silence=0.5:start_threshold=-50dB,"
            "silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-50dB,"
            "equalizer=f=2500:t=q:w=1.5:g=3,"  # Boost clarity frequencies
            "loudnorm=I=-14:TP=-1:LRA=11"  # Normalize to YouTube standard
        ),
        "-ar", "44100",
        str(processed),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        if result.returncode == 0 and processed.exists() and processed.stat().st_size > 10_000:
            audio_path.unlink(missing_ok=True)
            processed.rename(audio_path)
            logger.info("   Audio post-processing complete")
            return audio_path
    except Exception as exc:
        logger.warning(f"   Audio post-processing failed: {exc}")
        processed.unlink(missing_ok=True)

    return audio_path


def _probe_duration(path: Path) -> float:
    """Get audio duration in seconds."""
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", str(path),
        ]
        raw = subprocess.check_output(cmd, text=True, timeout=30)
        data = json.loads(raw)
        return float(data["format"]["duration"])
    except Exception:
        return 0.0


# ═══════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════

def generate_voice(script_text: str, channel: dict,
                   video_id: int | None = None) -> Path:
    """
    Generate voice audio for a script.
    Tries: ElevenLabs → Edge TTS → gTTS
    Then post-processes for quality.
    """
    channel_id = channel["channel_id"]
    language = channel.get("language", "es")

    # Determine output path
    channel_dir = CHANNEL_DIRS.get(channel_id)
    timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
    if channel_dir:
        out_path = channel_dir / "audio" / f"{timestamp}_voice.mp3"
    else:
        out_path = Path(f"{timestamp}_voice.mp3")

    # Clean script for TTS
    clean_text = _clean_script_for_tts(script_text)
    if not clean_text:
        raise ValueError("Script is empty after cleaning")

    logger.info(f"🔊 Generating voice for '{channel['name']}' ({len(clean_text)} chars)")

    tts_primary = env("TTS_PRIMARY", "edge").strip().lower()
    use_eleven = bool(env("ELEVENLABS_API_KEY")) and QUOTA.allow("elevenlabs", cost=1)

    chain = FallbackChain("tts-provider")
    if tts_primary == "elevenlabs":
        if use_eleven:
            chain.add("elevenlabs", lambda: _elevenlabs_tts(clean_text, out_path, channel))
        chain.add("edge-tts", lambda: _edge_tts(clean_text, out_path, channel))
    else:
        chain.add("edge-tts", lambda: _edge_tts(clean_text, out_path, channel))
        if use_eleven:
            chain.add("elevenlabs", lambda: _elevenlabs_tts(clean_text, out_path, channel))
    chain.add("gtts", lambda: _gtts_fallback(clean_text, out_path, language))
    provider, success = chain.run()
    if provider:
        logger.info("   ✅ %s succeeded", provider)

    if not success:
        raise RuntimeError("All TTS providers failed. Check API keys and dependencies.")

    # Post-process audio
    _postprocess_audio(out_path)

    # Get duration
    duration = _probe_duration(out_path)
    logger.info(f"   Audio duration: {duration:.1f}s ({duration/60:.1f} min)")

    if duration < 30:
        logger.warning("   ⚠️ Audio is very short (<30s). Script may need more content.")

    # Update video record
    if video_id:
        update_video(video_id, {
            "audio_path": str(out_path),
            "duration_seconds": duration,
            "status": "audio_ready",
        })
        log_pipeline_step(channel.get("id"), video_id, "voice_generator", "ok",
                          f"Audio generated: {duration:.1f}s")

    return out_path
