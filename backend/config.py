"""
YouTube Automation Pro — Global Configuration
Centralized settings, paths, and environment loading.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ── Project root & .env ──────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

# ── Output directories ───────────────────────────────────────
OUTPUT_DIR = ROOT / "output"
ASSETS_DIR = ROOT / "assets"
LOGS_DIR = ROOT / "logs"
DB_PATH = ROOT / "data" / "youtube_automation.db"

# Per-channel output dirs created on demand
CHANNEL_DIRS = {
    "impacto-mundial": OUTPUT_DIR / "channel_1_impacto_mundial",
    "mentes-rotas": OUTPUT_DIR / "channel_2_mentes_rotas",
    "el-loco-de-la-ia": OUTPUT_DIR / "channel_3_loco_ia",
    "mind-warp": OUTPUT_DIR / "channel_4_mind_warp",
    "wealth-files": OUTPUT_DIR / "channel_5_wealth_files",
    "dark-science": OUTPUT_DIR / "channel_6_dark_science",
}

# Ensure all dirs exist
for d in [OUTPUT_DIR, ASSETS_DIR, LOGS_DIR, DB_PATH.parent,
          ASSETS_DIR / "fonts", ASSETS_DIR / "music", ASSETS_DIR / "templates"]:
    d.mkdir(parents=True, exist_ok=True)
for d in CHANNEL_DIRS.values():
    for sub in ["scripts", "audio", "clips", "thumbnails", "videos"]:
        (d / sub).mkdir(parents=True, exist_ok=True)


# ── Environment helpers ──────────────────────────────────────
def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


# ── Operational Configuration ──────────────────────────
QUOTA_LIMITS = {
    "youtube_data_api": env_int("QUOTA_YOUTUBE_DATA_API_DAILY", 250),
    "pexels": env_int("QUOTA_PEXELS_DAILY", 500),
    "pixabay": env_int("QUOTA_PIXABAY_DAILY", 500),
    "elevenlabs": env_int("QUOTA_ELEVENLABS_DAILY", 400),
    "reddit": env_int("QUOTA_REDDIT_DAILY", 1000),
    "google_trends": env_int("QUOTA_GOOGLE_TRENDS_DAILY", 1000),
}

PIPELINE_CONFIG = {
    "channel_delay_seconds": env_int("PIPELINE_CHANNEL_DELAY_SECONDS", 90),
    "auto_pause_after_errors": env_int("PIPELINE_AUTO_PAUSE_AFTER_ERRORS", 3),
    "strict_mode": env_bool("PIPELINE_STRICT_MODE", False),
    "max_retries": env_int("PIPELINE_RETRIES", 3),
}

VIDEO_CONFIG = {
    "min_duration_seconds": env_int("VIDEO_MIN_DURATION_SECONDS", 240),
    "max_duration_seconds": env_int("VIDEO_MAX_DURATION_SECONDS", 1080),
    "bitrate_mbps": env_int("VIDEO_BITRATE_MBPS", 8),
    "target_resolution": env("VIDEO_TARGET_RESOLUTION", "1080p"),
}

BROLL_CONFIG = {
    "min_clips": env_int("BROLL_MIN_CLIPS", 12),
    "max_clips": env_int("BROLL_MAX_CLIPS", 28),
    "timeout_seconds": env_int("BROLL_TIMEOUT_SECONDS", 300),
}

AUDIO_CONFIG = {
    "chunk_size": env_int("AUDIO_CHUNK_SIZE", 1000),
    "bitrate_kbps": env_int("AUDIO_BITRATE_KBPS", 192),
    "sample_rate": env_int("AUDIO_SAMPLE_RATE", 44100),
    "allow_silent_fallback": env_bool("ALLOW_SILENT_FALLBACK", False),
}

SCRIPT_CONFIG = {
    "max_retries": env_int("SCRIPT_MAX_RETRIES", 2),
    "hide_errors": env_bool("SCRIPT_HIDE_ERRORS", True),
}

THUMBNAIL_CONFIG = {
    "max_retries": env_int("THUMBNAIL_MAX_RETRIES", 2),
    "fallback_color": env("THUMBNAIL_FALLBACK_COLOR", "#FF6B35"),
}

YOUTUBE_CONFIG = {
    "upload_timeout_seconds": env_int("YOUTUBE_UPLOAD_TIMEOUT_SECONDS", 1800),
    "retry_backoff_seconds": env_int("YOUTUBE_RETRY_BACKOFF_SECONDS", 60),
}

LOGGING_CONFIG = {
    "level": env("LOG_LEVEL", "INFO"),
    "file_retention_days": env_int("LOG_FILE_RETENTION_DAYS", 30),
    "enable_detailed_phase_logs": env_bool("ENABLE_DETAILED_PHASE_LOGS", True),
}

AGENT_CONFIG = {
    "max_concurrent": env_int("MAX_CONCURRENT_AGENTS", 10),
    "session_timeout_minutes": env_int("AGENT_SESSION_TIMEOUT_MINUTES", 120),
    "memory_buffer_mb": env_int("AGENT_MEMORY_BUFFER_MB", 256),
}

MONITORING_CONFIG = {
    "enable_monitoring": env_bool("ENABLE_MONITORING", False),
    "webhook_error_alerts": env("WEBHOOK_ERROR_ALERTS", ""),
    "webhook_success_reports": env("WEBHOOK_SUCCESS_REPORTS", ""),
}
