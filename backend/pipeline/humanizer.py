"""
YouTube Automation Pro - Humanizer
Post-processes generated text to reduce generic AI phrasing and enforce channel voice.
"""
from __future__ import annotations

import re


AI_PATTERNS = [
    r"\b(en este video|in this video)\b",
    r"\b(como hemos mencionado|as we(?:'ve| have) seen)\b",
    r"\b(la guía definitiva|the ultimate guide)\b",
    r"\b(fascinante|fascinating)\b",
    r"\b(exploramos juntos|we explore together)\b",
]


CHANNEL_OPENERS = {
    "impacto-mundial": "Lo que vas a escuchar estuvo oculto durante décadas.",
    "mentes-rotas": "El expediente oficial no cuenta esta parte del caso.",
    "el-loco-de-la-ia": "Esto lo puedes aplicar hoy y ver resultado en minutos.",
    "mind-warp": "Your brain is about to disagree with what the evidence shows.",
    "wealth-files": "The public story is convenient; the real numbers tell something else.",
    "dark-science": "This discovery is real, measured, and deeply unsettling.",
}


def humanize_text(text: str, channel_id: str) -> str:
    """Apply lightweight rule-based humanization to generated scripts/descriptions."""
    if not text:
        return text

    out = text.strip()

    # Remove common generic AI framing phrases
    for pattern in AI_PATTERNS:
        out = re.sub(pattern, "", out, flags=re.IGNORECASE)

    # Normalize punctuation rhythm
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)

    # If intro looks weak, force a stronger channel-specific opener
    first_line = out.splitlines()[0].strip() if out.splitlines() else ""
    if len(first_line) < 20:
        opener = CHANNEL_OPENERS.get(channel_id, "")
        if opener:
            out = f"{opener}\n\n{out}"

    return out.strip()


def humanize_title(title: str, channel_id: str) -> str:
    """Clean obvious title patterns and keep compact high-CTR phrasing."""
    if not title:
        return title

    out = title.strip().replace("  ", " ")
    out = re.sub(r"\b(la guía definitiva de|the ultimate guide to)\b", "", out, flags=re.IGNORECASE)
    out = re.sub(r"\b(\d+\s+cosas?\s+que)\b", "", out, flags=re.IGNORECASE)
    out = re.sub(r"\s{2,}", " ", out).strip(" -:")

    # Keep title short and punchy
    if len(out) > 70:
        out = out[:67].rsplit(" ", 1)[0] + "..."

    return out

