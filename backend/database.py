"""
YouTube Automation Pro — SQLite Database
Schema, initialization, and CRUD operations.
Replaces the broken MongoDB + JSON file approach from the old system.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import DB_PATH

# ═══════════════════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════════════════

SCHEMA = """
-- Canales de YouTube
CREATE TABLE IF NOT EXISTS channels (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id      TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    niche           TEXT NOT NULL,
    language        TEXT NOT NULL DEFAULT 'es',
    youtube_channel_url TEXT DEFAULT '',
    color_primary   TEXT DEFAULT '#6C63FF',
    color_secondary TEXT DEFAULT '#0A0A0F',
    color_accent    TEXT DEFAULT '#FFFFFF',
    tone            TEXT DEFAULT 'narrative',
    audience        TEXT DEFAULT '',
    frequency       TEXT DEFAULT '4/week',
    publish_hours   TEXT DEFAULT '[]',
    duration_min    INTEGER DEFAULT 10,
    duration_max    INTEGER DEFAULT 18,
    title_formula   TEXT DEFAULT '',
    hooks           TEXT DEFAULT '[]',
    broll_style     TEXT DEFAULT '',
    voice_id        TEXT DEFAULT 'EXAVITQu4vr4xnSDxMaL',
    voice_stability REAL DEFAULT 0.45,
    voice_similarity REAL DEFAULT 0.85,
    voice_style     REAL DEFAULT 0.3,
    tts_provider    TEXT DEFAULT 'elevenlabs',
    thumbnail_style TEXT DEFAULT 'cinematic',
    script_template TEXT DEFAULT '',
    seed_topics     TEXT DEFAULT '[]',
    category_id     TEXT DEFAULT '27',
    oauth_client_file TEXT DEFAULT '',
    oauth_token_file  TEXT DEFAULT '',
    privacy_status  TEXT DEFAULT 'public',
    subscribers     INTEGER DEFAULT 0,
    total_views     INTEGER DEFAULT 0,
    cpm_estimate    REAL DEFAULT 5.0,
    is_active       INTEGER DEFAULT 1,
    config_json     TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- Videos generados
CREATE TABLE IF NOT EXISTS videos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id      INTEGER REFERENCES channels(id),
    title           TEXT DEFAULT '',
    topic           TEXT DEFAULT '',
    script_text     TEXT DEFAULT '',
    script_path     TEXT DEFAULT '',
    audio_path      TEXT DEFAULT '',
    video_path      TEXT DEFAULT '',
    thumbnail_path  TEXT DEFAULT '',
    short_path      TEXT DEFAULT '',
    status          TEXT DEFAULT 'pending',
    youtube_video_id TEXT DEFAULT '',
    youtube_url     TEXT DEFAULT '',
    scheduled_at    TEXT,
    published_at    TEXT,
    views           INTEGER DEFAULT 0,
    likes           INTEGER DEFAULT 0,
    comments        INTEGER DEFAULT 0,
    ctr             REAL DEFAULT 0,
    retention       REAL DEFAULT 0,
    estimated_revenue REAL DEFAULT 0,
    duration_seconds REAL DEFAULT 0,
    metadata_json   TEXT DEFAULT '{}',
    error_message   TEXT DEFAULT '',
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

-- Tendencias detectadas
CREATE TABLE IF NOT EXISTS trends (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id      INTEGER REFERENCES channels(id),
    topic           TEXT NOT NULL,
    score           REAL DEFAULT 0,
    source          TEXT DEFAULT '',
    source_url      TEXT DEFAULT '',
    search_volume   INTEGER DEFAULT 0,
    growth_rate     REAL DEFAULT 0,
    competition     REAL DEFAULT 0,
    engagement      REAL DEFAULT 0,
    used            INTEGER DEFAULT 0,
    context_json    TEXT DEFAULT '{}',
    detected_at     TEXT DEFAULT (datetime('now'))
);

-- Logs del pipeline
CREATE TABLE IF NOT EXISTS pipeline_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id      INTEGER,
    video_id        INTEGER,
    step            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'running',
    message         TEXT DEFAULT '',
    duration_seconds REAL DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Uso de APIs
CREATE TABLE IF NOT EXISTS api_usage (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    service         TEXT NOT NULL,
    endpoint        TEXT DEFAULT '',
    tokens_used     INTEGER DEFAULT 0,
    chars_used      INTEGER DEFAULT 0,
    requests_used   INTEGER DEFAULT 1,
    cost_usd        REAL DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- Scheduled jobs
CREATE TABLE IF NOT EXISTS schedule (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id      INTEGER REFERENCES channels(id),
    video_id        INTEGER REFERENCES videos(id),
    scheduled_at    TEXT NOT NULL,
    status          TEXT DEFAULT 'pending',
    created_at      TEXT DEFAULT (datetime('now'))
);
"""

# ═══════════════════════════════════════════════════════════════
# 6 Channels Seed Data
# ═══════════════════════════════════════════════════════════════

SEED_CHANNELS = [
    {
        "channel_id": "impacto-mundial",
        "name": "Impacto Mundial",
        "niche": "Misterios históricos, conspiraciones gubernamentales, eventos inexplicables, lugares prohibidos",
        "language": "es",
        "youtube_channel_url": "https://www.youtube.com/@ImpactoMundial-y4b",
        "color_primary": "#C8A829",
        "color_secondary": "#0A0A0A",
        "color_accent": "#8B0000",
        "tone": "Narrativo, tenso, revelador, con pausas dramáticas",
        "audience": "Hispanohablantes 18-45 años, curiosos, amantes del misterio",
        "frequency": "5/week",
        "publish_hours": json.dumps(["20:00 ES mar", "20:00 ES jue", "11:00 ES sab"]),
        "duration_min": 10,
        "duration_max": 18,
        "title_formula": "[Dato impactante] + [Elemento prohibido/oculto] + [Promesa de revelación]",
        "hooks": json.dumps([
            "Lo que estás a punto de ver fue clasificado durante 50 años",
            "Nadie habla de esto y hay una razón",
            "Este descubrimiento cambió todo lo que creíamos saber"
        ]),
        "broll_style": "Imágenes satelitales, documentos desclasificados, ruinas, mapas antiguos",
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "voice_stability": 0.45,
        "voice_similarity": 0.85,
        "voice_style": 0.3,
        "thumbnail_style": "dramatic_aerial",
        "seed_topics": json.dumps([
            "La ciudad que desapareció en 24 horas y nadie sabe por qué",
            "El experimento que el gobierno ocultó durante 50 años",
            "Encontraron esto en el océano y los científicos no tienen explicación"
        ]),
        "category_id": "27",
        "cpm_estimate": 6.0,
    },
    {
        "channel_id": "mentes-rotas",
        "name": "Mentes Rotas",
        "niche": "True crime, asesinos en serie, casos sin resolver, psicología criminal, sectas",
        "language": "es",
        "color_primary": "#DC143C",
        "color_secondary": "#1A1A1A",
        "color_accent": "#E8E8E8",
        "tone": "Investigativo, oscuro, suspense constante, narrativa de detective",
        "audience": "Hispanohablantes 20-50 años, fascinados por la psicología oscura",
        "frequency": "4/week",
        "publish_hours": json.dumps(["20:00 ES vie", "22:00 ES dom"]),
        "duration_min": 15,
        "duration_max": 25,
        "title_formula": "[Nombre del caso/criminal] + [Dato perturbador] + [Pregunta sin respuesta]",
        "hooks": json.dumps([
            "Esta historia nunca llegó a los medios principales",
            "La policía cerró el caso pero los archivos dicen otra cosa",
            "Nadie se explica cómo pudo ocurrir esto durante tanto tiempo"
        ]),
        "broll_style": "Salas de investigación, archivos judiciales, mapas de crimen, fotografías de época",
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "voice_stability": 0.40,
        "voice_similarity": 0.90,
        "voice_style": 0.4,
        "thumbnail_style": "crime_documentary",
        "seed_topics": json.dumps([
            "El asesino que vivió entre nosotros 20 años sin que nadie lo supiera",
            "La familia que desapareció en ruta y nunca encontraron los cuerpos",
            "Por qué los psicópatas son encantadores: la ciencia lo explica"
        ]),
        "category_id": "27",
        "cpm_estimate": 5.5,
    },
    {
        "channel_id": "el-loco-de-la-ia",
        "name": "El Loco de la IA",
        "niche": "Herramientas de IA gratuitas, automatización, ganar dinero con IA, tutoriales prácticos",
        "language": "es",
        "color_primary": "#00E5FF",
        "color_secondary": "#0A0A0A",
        "color_accent": "#FFFFFF",
        "tone": "Entusiasta, directo, práctico, sin rodeos, resultados reales",
        "audience": "Emprendedores hispanohablantes 18-40 años",
        "frequency": "4/week",
        "publish_hours": json.dumps(["18:00 ES lun", "18:00 ES mie", "18:00 ES vie"]),
        "duration_min": 8,
        "duration_max": 14,
        "title_formula": "[Herramienta/método] + [Resultado en tiempo concreto] + [Elemento de sorpresa]",
        "hooks": json.dumps([
            "En los próximos 10 minutos vas a aprender lo que otros pagan miles de euros por saber",
            "Esta herramienta lleva 6 meses disponible y casi nadie la conoce",
            "Esto va a cambiar completamente tu forma de trabajar"
        ]),
        "broll_style": "Interfaces de software, pantallas con código, dashboards, gráficos de crecimiento",
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "voice_stability": 0.55,
        "voice_similarity": 0.75,
        "voice_style": 0.5,
        "thumbnail_style": "tech_futuristic",
        "seed_topics": json.dumps([
            "Esta IA hace en 3 minutos lo que un diseñador tarda 3 horas",
            "Gané 2.000 euros este mes con estas 5 herramientas de IA gratis",
            "ChatGPT tiene un modo secreto que muy pocos conocen"
        ]),
        "category_id": "28",
        "cpm_estimate": 8.0,
    },
    {
        "channel_id": "mind-warp",
        "name": "Mind Warp",
        "niche": "Psicología del comportamiento, dark psychology, sesgos cognitivos, manipulación",
        "language": "en",
        "color_primary": "#7B1FA2",
        "color_secondary": "#0A0A0A",
        "color_accent": "#FFFFFF",
        "tone": "Intelectual pero accesible, inquietante, revelador, datos científicos reales",
        "audience": "Global anglófona 18-45 años",
        "frequency": "5/week",
        "publish_hours": json.dumps(["15:00 UTC mar", "15:00 UTC jue", "15:00 UTC sab"]),
        "duration_min": 10,
        "duration_max": 16,
        "title_formula": "[Verdad contraintuitiva] + [Conexión vida cotidiana] + [Implicación perturbadora]",
        "hooks": json.dumps([
            "Your brain has been lying to you your entire life and here is the proof",
            "Psychologists discovered something about human behavior that changes everything",
            "This experiment was so disturbing it was banned from being repeated"
        ]),
        "broll_style": "Experimentos psicológicos, cerebros, laboratorios, personas en situaciones cotidianas",
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "voice_stability": 0.50,
        "voice_similarity": 0.85,
        "voice_style": 0.35,
        "thumbnail_style": "brain_neural",
        "seed_topics": json.dumps([
            "Why your brain lies to you every single day (and you can't stop it)",
            "The psychological trick billionaires use that nobody talks about",
            "What happens to your brain when you stop social media for 30 days"
        ]),
        "category_id": "27",
        "cpm_estimate": 12.0,
    },
    {
        "channel_id": "wealth-files",
        "name": "Wealth Files",
        "niche": "Mentalidad billonarios, rise and fall imperios empresariales, dark money, secretos del dinero",
        "language": "en",
        "color_primary": "#FFD700",
        "color_secondary": "#0A0A0A",
        "color_accent": "#E5E4E2",
        "tone": "Autoritario, revelador, datos concretos, aspiracional pero realista",
        "audience": "Global anglófona 22-50 años, aspiracional",
        "frequency": "5/week",
        "publish_hours": json.dumps(["14:00 UTC lun", "14:00 UTC mie"]),
        "duration_min": 12,
        "duration_max": 20,
        "title_formula": "[Nombre/cifra impactante] + [Secreto/verdad oculta] + [Implicación para el espectador]",
        "hooks": json.dumps([
            "Nobody talks about this because it destroys the narrative they want you to believe",
            "I studied 200 billionaires for 3 years and found one thing they all do differently",
            "The real reason most people will never be wealthy has nothing to do with money"
        ]),
        "broll_style": "Jets privados, oficinas de lujo, Wall Street, yates, mansiones, gráficos financieros",
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "voice_stability": 0.60,
        "voice_similarity": 0.80,
        "voice_style": 0.25,
        "thumbnail_style": "luxury_premium",
        "seed_topics": json.dumps([
            "How Elon Musk thinks differently from every other human alive",
            "The insane daily routine of the world's richest people",
            "What nobody tells you about how billionaires actually spend money"
        ]),
        "category_id": "27",
        "cpm_estimate": 15.0,
    },
    {
        "channel_id": "dark-science",
        "name": "Dark Science",
        "niche": "Misterios del universo, descubrimientos perturbadores, what-if, océano profundo, física cuántica",
        "language": "en",
        "color_primary": "#1565C0",
        "color_secondary": "#0A0A0A",
        "color_accent": "#00E5FF",
        "tone": "Documental científico de alta calidad, maravilla y terror simultáneos, accesible",
        "audience": "Global anglófona 16-40 años, curiosos intelectuales",
        "frequency": "4/week",
        "publish_hours": json.dumps(["16:00 UTC dom", "18:00 UTC mie"]),
        "duration_min": 12,
        "duration_max": 22,
        "title_formula": "[Descubrimiento/fenómeno] + [Por qué es perturbador] + [Implicación para la humanidad]",
        "hooks": json.dumps([
            "Scientists found something at the bottom of the ocean that they still can't explain",
            "If you understood what this discovery actually means you would not sleep tonight",
            "This breaks every law of physics we thought was absolute"
        ]),
        "broll_style": "Espacio, océano profundo, laboratorios de física, animaciones de fenómenos",
        "voice_id": "EXAVITQu4vr4xnSDxMaL",
        "voice_stability": 0.45,
        "voice_similarity": 0.88,
        "voice_style": 0.30,
        "thumbnail_style": "deep_space",
        "seed_topics": json.dumps([
            "What scientists found at the bottom of the ocean that terrified them",
            "If the sun disappeared right now, here's exactly what would happen",
            "The black hole that shouldn't exist according to physics"
        ]),
        "category_id": "28",
        "cpm_estimate": 10.0,
    },
]


# ═══════════════════════════════════════════════════════════════
# Connection & helpers
# ═══════════════════════════════════════════════════════════════

def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = _get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables and seed initial channel data."""
    with get_db() as conn:
        conn.executescript(SCHEMA)
        # Only seed if channels table is empty
        count = conn.execute("SELECT COUNT(*) FROM channels").fetchone()[0]
        if count == 0:
            for ch in SEED_CHANNELS:
                cols = ", ".join(ch.keys())
                placeholders = ", ".join(["?"] * len(ch))
                conn.execute(
                    f"INSERT INTO channels ({cols}) VALUES ({placeholders})",
                    list(ch.values()),
                )


def dict_from_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    """Convert sqlite3.Row to dict."""
    if row is None:
        return None
    return dict(row)


def dicts_from_rows(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    """Convert list of sqlite3.Row to list of dicts."""
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════════
# CRUD — Channels
# ═══════════════════════════════════════════════════════════════

def get_all_channels() -> list[dict]:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM channels ORDER BY id").fetchall()
        return dicts_from_rows(rows)


def get_channel(channel_id: str) -> dict | None:
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM channels WHERE channel_id = ?", (channel_id,)
        ).fetchone()
        return dict_from_row(row)


def get_channel_by_db_id(db_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM channels WHERE id = ?", (db_id,)).fetchone()
        return dict_from_row(row)


def update_channel(channel_id: str, data: dict) -> bool:
    allowed = {
        "name", "niche", "language", "youtube_channel_url", "color_primary",
        "color_secondary", "color_accent", "tone", "audience", "frequency",
        "publish_hours", "duration_min", "duration_max", "voice_id",
        "voice_stability", "voice_similarity", "voice_style", "tts_provider",
        "thumbnail_style", "seed_topics", "category_id", "privacy_status",
        "subscribers", "total_views", "cpm_estimate", "is_active", "config_json",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return False
    updates["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    with get_db() as conn:
        conn.execute(
            f"UPDATE channels SET {set_clause} WHERE channel_id = ?",
            [*updates.values(), channel_id],
        )
    return True


# ═══════════════════════════════════════════════════════════════
# CRUD — Videos
# ═══════════════════════════════════════════════════════════════

def create_video(channel_db_id: int, topic: str, title: str = "") -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO videos (channel_id, topic, title, status) VALUES (?, ?, ?, 'pending')",
            (channel_db_id, topic, title),
        )
        return cur.lastrowid


def update_video(video_id: int, data: dict) -> None:
    allowed = {
        "title", "topic", "script_text", "script_path", "audio_path",
        "video_path", "thumbnail_path", "short_path", "status",
        "youtube_video_id", "youtube_url", "scheduled_at", "published_at",
        "views", "likes", "comments", "ctr", "retention",
        "estimated_revenue", "duration_seconds", "metadata_json", "error_message",
    }
    updates = {k: v for k, v in data.items() if k in allowed}
    if not updates:
        return
    updates["updated_at"] = datetime.now().isoformat()
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    with get_db() as conn:
        conn.execute(
            f"UPDATE videos SET {set_clause} WHERE id = ?",
            [*updates.values(), video_id],
        )


def get_video(video_id: int) -> dict | None:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
        return dict_from_row(row)


def get_videos(channel_id: int | None = None, status: str | None = None,
               limit: int = 50, offset: int = 0) -> list[dict]:
    query = "SELECT v.*, c.channel_id as channel_slug, c.name as channel_name FROM videos v LEFT JOIN channels c ON v.channel_id = c.id WHERE 1=1"
    params: list = []
    if channel_id is not None:
        query += " AND v.channel_id = ?"
        params.append(channel_id)
    if status:
        query += " AND v.status = ?"
        params.append(status)
    query += " ORDER BY v.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return dicts_from_rows(rows)


def get_video_count(channel_id: int | None = None, status: str | None = None) -> int:
    query = "SELECT COUNT(*) FROM videos WHERE 1=1"
    params: list = []
    if channel_id is not None:
        query += " AND channel_id = ?"
        params.append(channel_id)
    if status:
        query += " AND status = ?"
        params.append(status)
    with get_db() as conn:
        return conn.execute(query, params).fetchone()[0]


def delete_video(video_id: int) -> bool:
    """Delete one video and related scheduler/log rows."""
    with get_db() as conn:
        exists = conn.execute("SELECT 1 FROM videos WHERE id = ?", (video_id,)).fetchone()
        if not exists:
            return False
        conn.execute("DELETE FROM schedule WHERE video_id = ?", (video_id,))
        conn.execute("DELETE FROM pipeline_logs WHERE video_id = ?", (video_id,))
        conn.execute("DELETE FROM videos WHERE id = ?", (video_id,))
    return True


def delete_all_videos() -> int:
    """Delete all videos and related scheduler/log rows. Returns deleted count."""
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
        conn.execute("DELETE FROM schedule WHERE video_id IS NOT NULL")
        conn.execute("DELETE FROM pipeline_logs WHERE video_id IS NOT NULL")
        conn.execute("DELETE FROM videos")
    return int(count)


# ═══════════════════════════════════════════════════════════════
# CRUD — Trends
# ═══════════════════════════════════════════════════════════════

def save_trend(channel_db_id: int, topic: str, score: float, source: str,
               context: dict | None = None) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO trends (channel_id, topic, score, source, context_json) VALUES (?, ?, ?, ?, ?)",
            (channel_db_id, topic, score, source, json.dumps(context or {})),
        )
        return cur.lastrowid


def get_trends(channel_db_id: int | None = None, unused_only: bool = True,
               limit: int = 20) -> list[dict]:
    query = "SELECT t.*, c.channel_id as channel_slug FROM trends t LEFT JOIN channels c ON t.channel_id = c.id WHERE 1=1"
    params: list = []
    if channel_db_id is not None:
        query += " AND t.channel_id = ?"
        params.append(channel_db_id)
    if unused_only:
        query += " AND t.used = 0"
    query += " ORDER BY t.score DESC LIMIT ?"
    params.append(limit)
    with get_db() as conn:
        return dicts_from_rows(conn.execute(query, params).fetchall())


def mark_trend_used(trend_id: int) -> None:
    with get_db() as conn:
        conn.execute("UPDATE trends SET used = 1 WHERE id = ?", (trend_id,))


# ═══════════════════════════════════════════════════════════════
# CRUD — Pipeline Logs
# ═══════════════════════════════════════════════════════════════

def log_pipeline_step(channel_id: int | None, video_id: int | None,
                      step: str, status: str, message: str = "",
                      duration: float = 0) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO pipeline_logs (channel_id, video_id, step, status, message, duration_seconds) VALUES (?, ?, ?, ?, ?, ?)",
            (channel_id, video_id, step, status, message, duration),
        )
        return cur.lastrowid


def get_recent_logs(limit: int = 100) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM pipeline_logs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return dicts_from_rows(rows)


# ═══════════════════════════════════════════════════════════════
# CRUD — API Usage
# ═══════════════════════════════════════════════════════════════

def log_api_usage(service: str, endpoint: str = "", tokens: int = 0,
                  chars: int = 0, requests: int = 1, cost: float = 0) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT INTO api_usage (service, endpoint, tokens_used, chars_used, requests_used, cost_usd) VALUES (?, ?, ?, ?, ?, ?)",
            (service, endpoint, tokens, chars, requests, cost),
        )


def get_api_usage_today(service: str | None = None) -> list[dict]:
    query = "SELECT service, SUM(tokens_used) as total_tokens, SUM(chars_used) as total_chars, SUM(requests_used) as total_requests, SUM(cost_usd) as total_cost FROM api_usage WHERE date(created_at) = date('now')"
    params: list = []
    if service:
        query += " AND service = ?"
        params.append(service)
    query += " GROUP BY service"
    with get_db() as conn:
        return dicts_from_rows(conn.execute(query, params).fetchall())


# ═══════════════════════════════════════════════════════════════
# Analytics helpers
# ═══════════════════════════════════════════════════════════════

def get_dashboard_stats() -> dict:
    """Aggregated stats for the main dashboard."""
    with get_db() as conn:
        total_videos = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
        published = conn.execute("SELECT COUNT(*) FROM videos WHERE status = 'published'").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM videos WHERE status = 'pending'").fetchone()[0]
        generating = conn.execute("SELECT COUNT(*) FROM videos WHERE status = 'generating'").fetchone()[0]
        errors = conn.execute("SELECT COUNT(*) FROM videos WHERE status = 'error'").fetchone()[0]
        total_views = conn.execute("SELECT COALESCE(SUM(views), 0) FROM videos").fetchone()[0]
        total_revenue = conn.execute("SELECT COALESCE(SUM(estimated_revenue), 0) FROM videos").fetchone()[0]

        # Per-channel stats
        channel_stats = dicts_from_rows(conn.execute("""
            SELECT c.id, c.channel_id, c.name, c.color_primary, c.language,
                   COUNT(v.id) as video_count,
                   COALESCE(SUM(v.views), 0) as total_views,
                   COALESCE(SUM(v.estimated_revenue), 0) as total_revenue,
                   COUNT(CASE WHEN v.status = 'published' THEN 1 END) as published_count,
                   COUNT(CASE WHEN v.status = 'error' THEN 1 END) as error_count
            FROM channels c
            LEFT JOIN videos v ON c.id = v.channel_id
            GROUP BY c.id
            ORDER BY c.id
        """).fetchall())

        return {
            "total_videos": total_videos,
            "published": published,
            "pending": pending,
            "generating": generating,
            "errors": errors,
            "total_views": total_views,
            "total_revenue": round(total_revenue, 2),
            "channels": channel_stats,
        }
