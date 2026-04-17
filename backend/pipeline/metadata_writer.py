"""
YouTube Automation Pro — Metadata Writer
Generates SEO-optimized titles, descriptions, tags, and timestamps.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from ..database import update_video, log_pipeline_step
from .humanizer import humanize_text, humanize_title

logger = logging.getLogger("metadata-writer")


# ── Power words by language ──────────────────────────────────
POWER_WORDS = {
    "es": [
        "secreto", "oculto", "prohibido", "revelación", "impactante",
        "nadie", "nunca", "verdad", "descubrir", "increíble",
        "peligroso", "misterioso", "sorprendente", "urgente", "exclusivo",
    ],
    "en": [
        "secret", "hidden", "forbidden", "shocking", "truth",
        "nobody", "never", "revealed", "incredible", "dangerous",
        "mysterious", "controversial", "urgent", "exclusive", "terrifying",
    ],
}


def generate_metadata(title: str, script_text: str, channel: dict,
                      video_id: int | None = None) -> dict:
    """
    Generate complete SEO metadata for a YouTube video.
    Returns: optimized title, description, tags, timestamps, category.
    """
    channel_id = channel["channel_id"]
    language = channel.get("language", "es")
    category_id = channel.get("category_id", "27")

    logger.info(f"📋 Generating metadata for '{channel['name']}'")

    # ── Title optimization ───────────────────────────────────
    optimized_title = humanize_title(_optimize_title(title, channel), channel_id)

    # ── Description ──────────────────────────────────────────
    # Extract SEO description from script if available
    seo_desc = _extract_section(script_text, "SEO DESCRIPTION")
    description = humanize_text(
        _build_description(optimized_title, seo_desc, script_text, channel),
        channel_id,
    )

    # ── Tags ─────────────────────────────────────────────────
    script_tags = _extract_section(script_text, "TAGS")
    tags = _build_tags(title, script_tags, channel)

    # ── Timestamps ───────────────────────────────────────────
    timestamps = _extract_timestamps(script_text)

    metadata = {
        "title": optimized_title[:100],
        "description": description[:5000],
        "tags": tags[:500],
        "category_id": category_id,
        "language": language,
        "timestamps": timestamps,
        "privacy_status": channel.get("privacy_status", "public"),
    }

    # Update video record
    if video_id:
        update_video(video_id, {
            "title": optimized_title,
            "metadata_json": json.dumps(metadata, ensure_ascii=False),
            "status": "metadata_ready",
        })
        log_pipeline_step(channel.get("id"), video_id, "metadata_writer", "ok",
                          f"Metadata generated: {len(tags)} tags")

    logger.info(f"   ✅ Title: {optimized_title}")
    logger.info(f"   ✅ Tags: {len(tags.split(','))} tags")

    return metadata


def _optimize_title(title: str, channel: dict) -> str:
    """Score and optimize title for CTR."""
    language = channel.get("language", "es")

    # Clean up
    title = title.strip().rstrip(".")
    if len(title) > 60:
        # Try to cut at a word boundary
        title = title[:57]
        last_space = title.rfind(" ")
        if last_space > 30:
            title = title[:last_space]
        title += "..."

    return title


def _build_description(title: str, seo_desc: str, script_text: str,
                       channel: dict) -> str:
    """Build SEO-optimized description."""
    language = channel.get("language", "es")
    channel_name = channel.get("name", "")

    # First 2 lines (visible without expanding)
    if seo_desc:
        first_lines = seo_desc[:200]
    else:
        first_lines = title

    # Extract timestamps from script
    timestamps = _extract_timestamps(script_text)
    timestamps_section = "\n".join(timestamps) if timestamps else ""

    # Build full description
    if language == "es":
        desc = f"""{first_lines}

{'⏱️ TIMESTAMPS' if timestamps_section else ''}
{timestamps_section}

📌 En este video:
{_bullet_points(script_text, language)}

👉 Suscríbete para más contenido: @{channel_name.replace(' ', '')}
🔔 Activa la campana para no perderte ningún video

#{'  #'.join(_niche_hashtags(channel))}
"""
    else:
        desc = f"""{first_lines}

{'⏱️ TIMESTAMPS' if timestamps_section else ''}
{timestamps_section}

📌 In this video:
{_bullet_points(script_text, language)}

👉 Subscribe for more: @{channel_name.replace(' ', '')}
🔔 Hit the bell to never miss a video

#{'  #'.join(_niche_hashtags(channel))}
"""

    return desc.strip()


def _bullet_points(script_text: str, language: str) -> str:
    """Extract key points from script for description."""
    # Look for section titles
    sections = re.findall(r'^##\s+(?:SECCIÓN|SECTION|CONTENIDO|CONTENT)\s*\d*\s*[—–-]*\s*(.*?)$',
                          script_text, re.MULTILINE | re.IGNORECASE)
    if sections:
        return "\n".join(f"• {s.strip()}" for s in sections[:6])

    # Fallback: extract first sentence of each paragraph
    paragraphs = [p.strip() for p in script_text.split("\n\n") if p.strip() and not p.startswith("#")]
    points = []
    for p in paragraphs[:5]:
        first_sentence = p.split(".")[0].strip()
        if len(first_sentence) > 20:
            points.append(f"• {first_sentence}")
    return "\n".join(points) if points else "• Contenido exclusivo" if language == "es" else "• Exclusive content"


def _niche_hashtags(channel: dict) -> list[str]:
    """Generate 3 niche-specific hashtags."""
    niche = channel.get("niche", "").lower()
    tags_map = {
        "impacto-mundial": ["misterios", "conspiraciones", "documentales"],
        "mentes-rotas": ["truecrime", "casosreales", "criminología"],
        "el-loco-de-la-ia": ["inteligenciaartificial", "IA", "tecnología"],
        "mind-warp": ["psychology", "darkpsychology", "mindset"],
        "wealth-files": ["wealth", "billionaire", "money"],
        "dark-science": ["science", "space", "discovery"],
    }
    return tags_map.get(channel["channel_id"], ["youtube", "viral", "trending"])


def _build_tags(title: str, script_tags: str, channel: dict) -> str:
    """Build optimized tag string."""
    tags = set()

    # From script
    if script_tags:
        for t in script_tags.split(","):
            clean = t.strip().strip("#").strip()
            if clean:
                tags.add(clean)

    # From title
    stop_words = {"the", "a", "an", "is", "and", "or", "in", "on", "to", "for",
                  "el", "la", "de", "en", "y", "que", "por", "un", "una", "con"}
    for word in title.split():
        clean = re.sub(r"[^\w]", "", word.lower())
        if clean and len(clean) > 2 and clean not in stop_words:
            tags.add(clean)

    # Add niche tags
    niche_tags = _niche_hashtags(channel)
    tags.update(niche_tags)

    # Combine and limit
    tag_list = sorted(tags)[:20]
    return ", ".join(tag_list)


def _extract_timestamps(script_text: str) -> list[str]:
    """Generate approximate timestamps from script structure."""
    sections = re.findall(r'^##\s+(.+?)$', script_text, re.MULTILINE)
    if not sections:
        return []

    # Filter out metadata sections
    skip = {"TITLES", "TÍTULOS", "SEO DESCRIPTION", "TAGS", "SHORT VERSION"}
    content_sections = [s for s in sections if s.upper().strip() not in skip]

    timestamps = []
    time_per_section = max(30, 600 // max(1, len(content_sections)))

    for idx, section in enumerate(content_sections[:8]):
        minutes = (idx * time_per_section) // 60
        seconds = (idx * time_per_section) % 60
        timestamps.append(f"{minutes}:{seconds:02d} {section.strip()}")

    return timestamps


def _extract_section(script: str, section_name: str) -> str:
    """Extract content from a named section in the script."""
    pattern = rf"##\s*{re.escape(section_name)}(.*?)(?=##|$)"
    match = re.search(pattern, script, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()[:500]
    return ""
