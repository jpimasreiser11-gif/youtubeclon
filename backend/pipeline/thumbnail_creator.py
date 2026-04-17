"""
YouTube Automation Pro — Thumbnail Creator
Generates professional thumbnails with channel branding,
3 layout variants, and CTR scoring.
"""
from __future__ import annotations

import logging
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from ..config import CHANNEL_DIRS, ASSETS_DIR
from ..database import log_pipeline_step, update_video

logger = logging.getLogger("thumbnail-creator")

# ── Channel brand colors ─────────────────────────────────────
CHANNEL_STYLES = {
    "impacto-mundial": {
        "bg_color": (10, 10, 15),
        "accent": (200, 168, 41),
        "text_color": (255, 255, 255),
        "overlay_opacity": 180,
        "gradient_top": (139, 0, 0),
        "gradient_bottom": (10, 10, 15),
    },
    "mentes-rotas": {
        "bg_color": (15, 5, 5),
        "accent": (220, 20, 60),
        "text_color": (255, 255, 255),
        "overlay_opacity": 160,
        "gradient_top": (220, 20, 60),
        "gradient_bottom": (15, 5, 5),
    },
    "el-loco-de-la-ia": {
        "bg_color": (5, 10, 20),
        "accent": (0, 229, 255),
        "text_color": (255, 255, 255),
        "overlay_opacity": 170,
        "gradient_top": (0, 100, 200),
        "gradient_bottom": (5, 10, 20),
    },
    "mind-warp": {
        "bg_color": (10, 5, 20),
        "accent": (123, 31, 162),
        "text_color": (255, 255, 255),
        "overlay_opacity": 170,
        "gradient_top": (123, 31, 162),
        "gradient_bottom": (10, 5, 20),
    },
    "wealth-files": {
        "bg_color": (10, 10, 5),
        "accent": (255, 215, 0),
        "text_color": (255, 255, 255),
        "overlay_opacity": 160,
        "gradient_top": (180, 150, 0),
        "gradient_bottom": (10, 10, 5),
    },
    "dark-science": {
        "bg_color": (5, 5, 15),
        "accent": (21, 101, 192),
        "text_color": (255, 255, 255),
        "overlay_opacity": 170,
        "gradient_top": (0, 100, 200),
        "gradient_bottom": (5, 5, 15),
    },
}


def _get_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Try to load a good font, fall back to default."""
    font_names = [
        "Impact", "impact.ttf",
        "Arial Bold", "arialbd.ttf",
        "Segoe UI Bold", "segoeuib.ttf",
        "DejaVuSans-Bold.ttf",
    ]
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _extract_thumbnail_words(title: str) -> str:
    """Extract the 3-4 most impactful words for the thumbnail."""
    # Remove common stop words
    stop_words = {
        "the", "a", "an", "is", "was", "are", "were", "be", "been",
        "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
        "el", "la", "los", "las", "un", "una", "de", "del", "en", "y",
        "que", "por", "para", "con", "esta", "este", "ese", "esa",
        "what", "how", "why", "when", "who", "your", "you", "they",
    }
    words = [w for w in re.findall(r'\b\w+\b', title) if w.lower() not in stop_words]
    # Take the most impactful words (longest or most unique)
    words.sort(key=len, reverse=True)
    selected = words[:4]
    # Rebuild in original order
    original_words = title.split()
    result = [w for w in original_words if any(s.lower() == w.lower() for s in selected)]
    return " ".join(result[:4]).upper()


def _draw_text_with_outline(draw: ImageDraw.ImageDraw, position: tuple,
                            text: str, font: ImageFont.FreeTypeFont,
                            fill: tuple, outline: tuple = (0, 0, 0),
                            outline_width: int = 8):
    """Draw text with thick outline for readability."""
    x, y = position
    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx * dx + dy * dy <= outline_width * outline_width:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
    # Draw main text
    draw.text(position, text, font=font, fill=fill)


def _create_gradient_bg(width: int, height: int, top_color: tuple,
                         bottom_color: tuple) -> Image.Image:
    """Create a gradient background image."""
    img = Image.new("RGB", (width, height))
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        for x in range(width):
            img.putpixel((x, y), (r, g, b))
    return img


def _create_variant_a(text: str, style: dict, width: int = 1280, height: int = 720) -> Image.Image:
    """Variant A: Text at top with solid accent bar."""
    img = _create_gradient_bg(width, height, style["gradient_top"], style["gradient_bottom"])
    draw = ImageDraw.Draw(img)

    # Accent bar at top
    bar_height = 120
    draw.rectangle([(0, 0), (width, bar_height)], fill=style["accent"])

    # Add some visual elements
    draw.rectangle([(40, bar_height + 40), (width - 40, height - 40)],
                   outline=(*style["accent"], 100), width=3)

    # Text in accent bar
    font = _get_font(72)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    tx = (width - tw) // 2
    _draw_text_with_outline(draw, (tx, 20), text, font,
                            fill=style["text_color"], outline=(0, 0, 0), outline_width=6)

    return img


def _create_variant_b(text: str, style: dict, width: int = 1280, height: int = 720) -> Image.Image:
    """Variant B: Text at bottom with dark overlay."""
    img = _create_gradient_bg(width, height, style["gradient_top"], style["gradient_bottom"])
    draw = ImageDraw.Draw(img)

    # Dark overlay at bottom
    overlay = Image.new("RGBA", (width, 250), (0, 0, 0, style["overlay_opacity"]))
    img_rgba = img.convert("RGBA")
    img_rgba.paste(overlay, (0, height - 250), overlay)
    img = img_rgba.convert("RGB")
    draw = ImageDraw.Draw(img)

    # Accent line
    draw.rectangle([(0, height - 255), (width, height - 250)], fill=style["accent"])

    # Text at bottom
    font = _get_font(80)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    tx = (width - tw) // 2
    _draw_text_with_outline(draw, (tx, height - 200), text, font,
                            fill=style["text_color"], outline=(0, 0, 0), outline_width=10)

    return img


def _create_variant_c(text: str, style: dict, width: int = 1280, height: int = 720) -> Image.Image:
    """Variant C: Large centered text, no overlay."""
    img = _create_gradient_bg(width, height, style["bg_color"], style["gradient_top"])
    draw = ImageDraw.Draw(img)

    # Decorative elements
    draw.ellipse([(width // 2 - 250, height // 2 - 250),
                  (width // 2 + 250, height // 2 + 250)],
                 outline=(*style["accent"], 60), width=2)

    # Large centered text
    font = _get_font(96)
    # Word wrap if needed
    words = text.split()
    if len(words) > 2:
        line1 = " ".join(words[:2])
        line2 = " ".join(words[2:])
        for line, y_offset in [(line1, -60), (line2, 50)]:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            tx = (width - tw) // 2
            _draw_text_with_outline(draw, (tx, height // 2 + y_offset), line, font,
                                    fill=style["accent"], outline=(0, 0, 0), outline_width=12)
    else:
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        tx = (width - tw) // 2
        _draw_text_with_outline(draw, (tx, height // 2 - 40), text, font,
                                fill=style["accent"], outline=(0, 0, 0), outline_width=12)

    return img


def _score_thumbnail(img: Image.Image) -> float:
    """Score a thumbnail for estimated CTR (0-100)."""
    score = 50.0  # Base score

    # Check overall brightness contrast
    grayscale = img.convert("L")
    histogram = grayscale.histogram()
    dark_pixels = sum(histogram[:64]) / sum(histogram) * 100
    bright_pixels = sum(histogram[192:]) / sum(histogram) * 100

    # Good contrast = mix of dark and bright
    if dark_pixels > 30 and bright_pixels > 10:
        score += 15
    elif dark_pixels > 20:
        score += 8

    # Color vibrancy
    r, g, b = img.split()[:3]
    r_mean = sum(i * n for i, n in enumerate(r.histogram())) / max(1, sum(r.histogram()))
    g_mean = sum(i * n for i, n in enumerate(g.histogram())) / max(1, sum(g.histogram()))
    b_mean = sum(i * n for i, n in enumerate(b.histogram())) / max(1, sum(b.histogram()))
    color_spread = max(r_mean, g_mean, b_mean) - min(r_mean, g_mean, b_mean)
    if color_spread > 50:
        score += 15
    elif color_spread > 25:
        score += 8

    # Warm colors bonus (red/orange/yellow tend to get more clicks)
    if r_mean > g_mean and r_mean > b_mean:
        score += 10

    return min(100.0, score)


# ═══════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════

def create_thumbnails(title: str, channel: dict,
                      video_id: int | None = None) -> Path:
    """
    Generate 3 thumbnail variants and select the best one.
    Returns path to the best thumbnail.
    """
    channel_id = channel["channel_id"]
    style = CHANNEL_STYLES.get(channel_id, CHANNEL_STYLES["mind-warp"])

    logger.info(f"🖼️  Creating thumbnails for '{channel['name']}'")

    # Extract impactful words
    text = _extract_thumbnail_words(title)
    if not text:
        text = title[:30].upper()

    # Generate 3 variants
    variants = [
        ("A", _create_variant_a(text, style)),
        ("B", _create_variant_b(text, style)),
        ("C", _create_variant_c(text, style)),
    ]

    # Score and save all variants
    channel_dir = CHANNEL_DIRS.get(channel_id)
    timestamp = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")

    best_score = 0
    best_path = None
    variant_scores: list[dict] = []

    for label, img in variants:
        score = _score_thumbnail(img)
        if channel_dir:
            path = channel_dir / "thumbnails" / f"{timestamp}_thumb_{label}.jpg"
        else:
            path = Path(f"{timestamp}_thumb_{label}.jpg")
        path.parent.mkdir(parents=True, exist_ok=True)
        img.save(path, "JPEG", quality=95)

        logger.info(f"   Variant {label}: CTR score {score:.0f}/100 → {path.name}")
        variant_scores.append({"variant": label, "score": round(score, 2), "path": str(path)})

        if score > best_score:
            best_score = score
            best_path = path

    if not best_path:
        raise RuntimeError("Failed to create any thumbnail")

    logger.info(f"   ✅ Best thumbnail: {best_path.name} (score: {best_score:.0f})")

    # Save scoring artifact for future A/B analysis.
    if channel_dir:
        scores_path = channel_dir / "thumbnails" / f"{timestamp}_thumb_scores.json"
        scores_path.write_text(
            json.dumps(
                {
                    "title": title,
                    "selected": str(best_path),
                    "selected_score": round(best_score, 2),
                    "variants": variant_scores,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    # Update video record
    if video_id:
        update_video(video_id, {
            "thumbnail_path": str(best_path),
            "status": "thumbnail_ready",
        })
        log_pipeline_step(channel.get("id"), video_id, "thumbnail_creator", "ok",
                          f"Thumbnail created: CTR score {best_score:.0f}/100")

    return best_path
