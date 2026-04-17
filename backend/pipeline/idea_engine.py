"""
YouTube Automation Pro — Viral Idea Engine
Genera ideas reales y virales para cada nicho usando IA gratis (Gemini).

Estrategias de generación:
1. Trending Hooks — Ideas basadas en eventos actuales y tendencias
2. Evergreen Magnets — Ideas atemporales con alto potencial de búsqueda
3. Controversy Sparks — Temas polémicos que generan debate y engagement
4. Curiosity Gaps — Títulos que explotan el "knowledge gap" psicológico
5. Fear & FOMO — Ideas que activan urgencia y miedo a perderse algo
6. Story-Driven — Narrativas reales con arco dramático incorporado
"""
from __future__ import annotations

import json
import logging
import random
import re
import time
from datetime import datetime
from typing import Any

import requests

from ..config import env
from ..database import get_db, log_api_usage, log_pipeline_step

logger = logging.getLogger("idea-engine")


# ═══════════════════════════════════════════════════════════════
# Niche DNA — configuración profunda por canal
# ═══════════════════════════════════════════════════════════════

NICHE_DNA = {
    "impacto-mundial": {
        "name": "Impacto Mundial",
        "lang": "es",
        "core_themes": [
            "misterios sin resolver", "conspiraciones reales documentadas",
            "eventos inexplicables", "lugares prohibidos del mundo",
            "documentos desclasificados", "civilizaciones perdidas",
            "fenómenos paranormales con evidencia", "secretos gubernamentales",
            "descubrimientos arqueológicos perturbadores", "accidentes encubiertos",
        ],
        "viral_formulas": [
            "Lo que encontraron en {lugar} no debería existir",
            "Este documento desclasificado revela lo que {organización} hizo en {año}",
            "El misterio de {evento} que nadie pudo resolver en {X} años",
            "{X} cosas que {gobierno/organización} no quiere que sepas",
            "La verdad sobre {evento histórico} que los libros no cuentan",
            "Filmaron esto en {lugar} y los científicos no tienen explicación",
        ],
        "power_words": [
            "desclasificado", "prohibido", "oculto", "censurado", "borrado",
            "clasificado", "expediente", "evidencia", "encubierto", "revelado",
        ],
        "competitor_channels": [
            "Mundo Desconocido", "Leyendas Urbanas", "Terror en el Mundo",
            "Documentales Impactantes", "MrBallen en español",
        ],
        "trending_sources": [
            "declassified documents 2026", "archaeological discoveries",
            "unexplained phenomena caught on camera",
            "government secrets revealed", "abandoned places mysteries",
        ],
    },
    "mentes-rotas": {
        "name": "Mentes Rotas",
        "lang": "es",
        "core_themes": [
            "asesinos en serie documentados", "casos sin resolver famosos",
            "psicología criminal", "sectas destructivas", "desapariciones misteriosas",
            "crímenes pasionales", "interrogatorios reales", "errores judiciales",
            "perfiles criminales", "casos cold case resueltos con ADN",
        ],
        "viral_formulas": [
            "El caso de {nombre}: {X} años sin respuesta",
            "Lo que {criminal} dijo en su último interrogatorio te helará la sangre",
            "La policía encontró esto en {lugar} y el caso tomó un giro inesperado",
            "Vivió con {criminal} {X} años sin saber quién era realmente",
            "El error que cometió {criminal} y que lo delató después de {X} años",
            "{número} señales de alerta que todos ignoraron en el caso {nombre}",
        ],
        "power_words": [
            "perturbador", "escalofriante", "sin resolver", "confesión",
            "evidencia", "sospechoso", "víctima", "interrogatorio", "caso frío",
        ],
        "competitor_channels": [
            "Criminalmente", "Relatos de la Noche", "Dross",
            "JJ Macías Criminal", "Estela de Crímenes",
        ],
        "trending_sources": [
            "true crime cases 2026", "cold cases solved DNA",
            "serial killer documentaries", "criminal psychology studies",
        ],
    },
    "el-loco-de-la-ia": {
        "name": "El Loco de la IA",
        "lang": "es",
        "core_themes": [
            "herramientas de IA gratuitas", "automatización con IA",
            "ganar dinero con IA", "IA para productividad", "ChatGPT trucos avanzados",
            "creación de contenido con IA", "IA para freelancers",
            "negocios automatizados con IA", "IA vs trabajos tradicionales",
            "tutoriales paso a paso de herramientas IA",
        ],
        "viral_formulas": [
            "Esta IA hace en {X} minutos lo que un {profesión} tarda {X} horas",
            "Gané {cantidad}€ este mes usando solo estas {X} herramientas de IA gratis",
            "{herramienta} tiene un modo secreto que {X}% de usuarios no conoce",
            "Reemplaza estas {X} herramientas de pago con esta IA gratuita",
            "Automaticé mi negocio entero con IA: gano {cantidad}€/mes sin trabajar",
            "La IA que está destruyendo a {industria}: así puedes aprovecharla",
        ],
        "power_words": [
            "gratis", "secreto", "automatizar", "minutos", "sin experiencia",
            "paso a paso", "resultados", "dinero", "reemplaza", "truco",
        ],
        "competitor_channels": [
            "Dot CSV", "Carlos Slim IA", "Romuald Fons",
            "Matt Wolfe", "AI Andy en español",
        ],
        "trending_sources": [
            "new AI tools free 2026", "ChatGPT hacks",
            "AI automation business", "make money with AI",
            "best free AI tools launched this week",
        ],
    },
    "mind-warp": {
        "name": "Mind Warp",
        "lang": "en",
        "core_themes": [
            "cognitive biases in everyday life", "dark psychology tactics",
            "manipulation techniques people use unknowingly",
            "neuroscience discoveries about human behavior",
            "psychological experiments that changed everything",
            "social engineering and persuasion", "body language secrets",
            "subconscious patterns that control decisions",
            "psychology of addiction and habits", "emotional intelligence dark side",
        ],
        "viral_formulas": [
            "Your brain has been lying to you about {topic} and here is the proof",
            "The {experiment/study} that was so disturbing it got banned",
            "{X} psychological tricks {grupo} uses that you fall for every day",
            "Why {common belief} is actually a cognitive bias controlling your life",
            "Psychologists discovered {hallazgo} and it changes everything",
            "The dark psychology behind {fenómeno cotidiano} nobody talks about",
        ],
        "power_words": [
            "manipulation", "subconscious", "cognitive bias", "disturbing",
            "experiment", "banned", "rewire", "dark", "hidden", "proven",
        ],
        "competitor_channels": [
            "Psych2Go", "Better Than Yesterday", "Einzelgänger",
            "Sprouts", "Academy of Ideas",
        ],
        "trending_sources": [
            "psychology studies 2026", "neuroscience discoveries",
            "cognitive bias research", "social psychology experiments",
            "dark psychology techniques",
        ],
    },
    "wealth-files": {
        "name": "Wealth Files",
        "lang": "en",
        "core_themes": [
            "billionaire mindset and habits", "rise and fall of empires",
            "dark money and financial secrets", "investment strategies of the ultra-rich",
            "entrepreneur failure stories and comebacks",
            "corporate scandals and fraud", "wealth inequality hidden mechanics",
            "financial literacy secrets schools don't teach",
            "side hustle to empire stories", "crypto and new money secrets",
        ],
        "viral_formulas": [
            "How {nombre} went from {situación} to ${cantidad} in {X} years",
            "The ${cantidad} mistake that destroyed {empresa/persona}",
            "{X} rules rich people follow that poor people ignore",
            "I studied {X} billionaires for {X} years: here's what they all do differently",
            "The real reason {persona famosa} is worth ${cantidad} (it's not what you think)",
            "Why {país/ciudad} is secretly the richest place on Earth",
        ],
        "power_words": [
            "billionaire", "secret", "wealth", "empire", "destroyed",
            "million", "strategy", "hidden", "insider", "compound",
        ],
        "competitor_channels": [
            "Business Casual", "Company Man", "Graham Stephan",
            "Magnates Media", "Modern MBA",
        ],
        "trending_sources": [
            "billionaire news 2026", "startup failures",
            "financial scandals", "wealth building strategies",
            "richest people net worth changes",
        ],
    },
    "dark-science": {
        "name": "Dark Science",
        "lang": "en",
        "core_themes": [
            "deep ocean mysteries", "space discoveries that defy physics",
            "quantum physics paradoxes explained", "what-if scenarios",
            "extinct species that might still exist", "alien life evidence",
            "black holes and singularities", "time travel theoretical physics",
            "AI singularity and existential risk", "doomsday scenarios backed by science",
        ],
        "viral_formulas": [
            "Scientists found {descubrimiento} and they still can't explain it",
            "What would happen if {escenario imposible} actually occurred",
            "This {fenómeno} breaks every law of physics we thought was absolute",
            "NASA just released {dato} and nobody is talking about it",
            "The {lugar/objeto} that shouldn't exist according to science",
            "We were wrong about {concepto científico} for {X} years: here's why",
        ],
        "power_words": [
            "terrifying", "impossible", "anomaly", "breakthrough",
            "paradox", "singularity", "extinct", "infinite", "quantum", "void",
        ],
        "competitor_channels": [
            "Kurzgesagt", "Veritasium", "Ridddle",
            "SEA", "What If",
        ],
        "trending_sources": [
            "space discoveries 2026", "deep ocean exploration",
            "quantum physics breakthrough", "NASA announcements",
            "AI existential risk news",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════
# 6 Estrategias de Generación
# ═══════════════════════════════════════════════════════════════

STRATEGIES = {
    "trending_hooks": {
        "name_es": "Trending Hooks",
        "name_en": "Trending Hooks",
        "description": "Ideas basadas en eventos actuales y noticias virales del nicho",
        "prompt_template": """Eres un estratega de YouTube viral con 10 años de experiencia. 
Genera {count} ideas de videos REALES y ACTUALES para un canal de YouTube en el nicho: "{niche}".

IDIOMA DEL CONTENIDO: {lang_label}

REGLAS CRÍTICAS:
- Las ideas deben estar basadas en eventos REALES, descubrimientos REALES o noticias REALES de 2025-2026
- NO inventes datos. Basa todo en hechos verificables
- Cada idea debe tener un ángulo único que no hayan cubierto otros canales
- Piensa en qué buscaría la gente en YouTube AHORA MISMO sobre este tema

TEMAS BASE DEL CANAL: {themes}

CANALES COMPETIDORES (genera ideas mejores que las de ellos): {competitors}

Para cada idea, devuelve un JSON array con objetos que tengan:
- "title": título optimizado para CTR (máximo 60 chars), en {lang_label}
- "hook": frase de apertura del video (máximo 20 palabras), en {lang_label}
- "angle": ángulo único que diferencia esta idea (1 frase), en {lang_label}
- "why_viral": por qué esta idea se haría viral (1 frase), en {lang_label}
- "search_potential": estimación de volumen de búsqueda (alto/medio/bajo)
- "strategy": "trending_hooks"
- "virality_score": puntuación de 0 a 100

Responde SOLO con el JSON array, sin texto adicional ni markdown.""",
    },
    "evergreen_magnets": {
        "name_es": "Imanes Evergreen",
        "name_en": "Evergreen Magnets",
        "description": "Ideas atemporales con alto potencial de búsqueda perpetua",
        "prompt_template": """Eres un experto en SEO de YouTube y contenido evergreen.
Genera {count} ideas de videos EVERGREEN (que funcionen igual de bien dentro de 2 años) para un canal de "{niche}".

IDIOMA DEL CONTENIDO: {lang_label}

REGLAS:
- Temas que la gente busca CONSTANTEMENTE, no solo ahora
- Preguntas que la gente se hace una y otra vez
- Contenido educativo o informativo de alto valor
- Títulos optimizados para búsqueda orgánica de YouTube

TEMÁTICAS DEL CANAL: {themes}

Devuelve JSON array con objetos:
- "title": título SEO-optimizado (máx 60 chars), en {lang_label}
- "hook": frase de apertura (máx 20 palabras), en {lang_label}
- "angle": ángulo único, en {lang_label}
- "why_viral": potencial de viralidad, en {lang_label}
- "search_potential": alto/medio/bajo
- "strategy": "evergreen_magnets"
- "virality_score": 0-100

Responde SOLO con JSON array.""",
    },
    "controversy_sparks": {
        "name_es": "Chispas de Controversia",
        "name_en": "Controversy Sparks",
        "description": "Temas polémicos que generan debate y alto engagement en comentarios",
        "prompt_template": """Eres un productor de contenido viral especializado en temas que generan DEBATE.
Genera {count} ideas de videos POLÉMICOS (pero no ofensivos) para un canal de "{niche}".

IDIOMA DEL CONTENIDO: {lang_label}

REGLAS:
- Temas que dividen opiniones y generan MUCHOS comentarios
- Presentar ambos lados pero con una postura firme
- Evitar temas de odio, política extrema o discriminación
- El objetivo es debate intelectual, no toxicidad
- Ideas que la gente NECESITA compartir para defender su posición

TEMÁTICAS: {themes}

Devuelve JSON array:
- "title": título provocador (máx 60 chars), en {lang_label}
- "hook": apertura que polariza inmediatamente, en {lang_label}
- "angle": por qué esto genera debate, en {lang_label}
- "why_viral": mecánica del engagement, en {lang_label}
- "search_potential": alto/medio/bajo
- "strategy": "controversy_sparks"
- "virality_score": 0-100

SOLO JSON array.""",
    },
    "curiosity_gaps": {
        "name_es": "Brechas de Curiosidad",
        "name_en": "Curiosity Gaps",
        "description": "Títulos que explotan el vacío de conocimiento y obligan a hacer clic",
        "prompt_template": """Eres un psicólogo del clickbait ÉTICO especializado en "curiosity gaps".
Genera {count} ideas de videos que explotan la brecha de curiosidad para un canal de "{niche}".

IDIOMA DEL CONTENIDO: {lang_label}

REGLAS:
- El título debe crear una NECESIDAD irresistible de saber la respuesta
- Usar: "por qué...", "qué pasa si...", "lo que nadie sabe sobre..."
- El contenido DEBE cumplir la promesa del título (no clickbait vacío)
- Cada idea debe revelar algo que genuinamente sorprenda

TEMÁTICAS: {themes}

Devuelve JSON array:
- "title": título con curiosity gap (máx 60 chars), en {lang_label}
- "hook": pregunta o dato que abre la brecha, en {lang_label}
- "angle": la sorpresa/revelación real, en {lang_label}
- "why_viral": psicología detrás del clic, en {lang_label}
- "search_potential": alto/medio/bajo
- "strategy": "curiosity_gaps"
- "virality_score": 0-100

SOLO JSON array.""",
    },
    "fear_fomo": {
        "name_es": "Miedo y FOMO",
        "name_en": "Fear & FOMO",
        "description": "Ideas que activan urgencia, miedo a perderse algo, o preocupación real",
        "prompt_template": """Eres un estratega de contenido experto en activar FOMO y urgencia.
Genera {count} ideas de videos que activen el miedo a perderse algo o preocupación real para "{niche}".

IDIOMA DEL CONTENIDO: {lang_label}

REGLAS:
- Temas donde el espectador siente que NECESITA ver esto YA
- Información que cambiará su perspectiva o le protegerá
- Urgencia real, no fabricada — temas con base factual
- El espectador debe sentir que perder este video le costará algo

TEMÁTICAS: {themes}

Devuelve JSON array:
- "title": título con urgencia (máx 60 chars), en {lang_label}
- "hook": dato que genera urgencia inmediata, en {lang_label}
- "angle": por qué es urgente, en {lang_label}
- "why_viral": mecánica del FOMO, en {lang_label}
- "search_potential": alto/medio/bajo
- "strategy": "fear_fomo"
- "virality_score": 0-100

SOLO JSON array.""",
    },
    "story_driven": {
        "name_es": "Narrativas Reales",
        "name_en": "Story-Driven",
        "description": "Historias reales con arco dramático que enganchan de principio a fin",
        "prompt_template": """Eres un guionista de documentales virales.
Genera {count} ideas de videos basados en HISTORIAS REALES con arco dramático completo para "{niche}".

IDIOMA DEL CONTENIDO: {lang_label}

REGLAS:
- Cada idea debe basarse en una historia REAL (persona, evento, caso)
- La historia debe tener: planteamiento, nudo, clímax y desenlace
- Historias poco conocidas pero fascinantes
- El arco emocional debe mantener al espectador hasta el final
- Prioriza historias con giros inesperados

TEMÁTICAS: {themes}

Devuelve JSON array:
- "title": título narrativo (máx 60 chars), en {lang_label}
- "hook": el momento más impactante de la historia, en {lang_label}
- "angle": el giro inesperado, en {lang_label}
- "why_viral": por qué esta historia engancha, en {lang_label}
- "search_potential": alto/medio/bajo
- "strategy": "story_driven"
- "virality_score": 0-100

SOLO JSON array.""",
    },
}


# ═══════════════════════════════════════════════════════════════
# Generación con Gemini (gratis)
# ═══════════════════════════════════════════════════════════════

def _call_gemini(prompt: str, max_retries: int = 3) -> str | None:
    """Call Gemini API with retry and model fallback for rate limits."""
    api_key = env("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY not configured")
        return None

    from google import genai
    client = genai.Client(api_key=api_key)

    # Try primary model, fallback to lite if rate-limited
    models = ["gemini-2.0-flash", "gemini-2.0-flash-lite"]

    for model in models:
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                )
                text = (response.text or "").strip()
                log_api_usage("gemini", "idea_engine", chars=len(prompt) + len(text))
                if text:
                    return text
            except Exception as exc:
                exc_str = str(exc)
                if "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str:
                    wait = min(60, 15 * attempt)
                    logger.warning(f"   Rate limited on {model} (attempt {attempt}). Waiting {wait}s...")
                    time.sleep(wait)
                    if attempt == max_retries:
                        logger.info(f"   Switching from {model} to next model...")
                        break  # Try next model
                else:
                    logger.error(f"Gemini API error ({model}): {exc}")
                    return None

    logger.error("All Gemini models exhausted after retries")
    return None


def _parse_ideas_json(raw: str) -> list[dict]:
    """Parse JSON from Gemini response, handling markdown code fences."""
    if not raw:
        return []

    # Strip markdown code fences
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "ideas" in data:
            return data["ideas"]
        return []
    except json.JSONDecodeError:
        # Try to find JSON array in the text
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.warning(f"Could not parse JSON from Gemini response ({len(text)} chars)")
        return []


# ═══════════════════════════════════════════════════════════════
# Virality Scoring Enhancement
# ═══════════════════════════════════════════════════════════════

def _enhance_score(idea: dict, niche_dna: dict) -> float:
    """
    Enhance the AI's virality score with heuristic analysis.
    Checks title quality, power words, length, strategy value.
    """
    base_score = float(idea.get("virality_score", 50))
    title = idea.get("title", "")
    bonus = 0.0

    # Title length sweet spot (40-58 chars)
    tlen = len(title)
    if 40 <= tlen <= 58:
        bonus += 8
    elif 30 <= tlen <= 65:
        bonus += 4

    # Contains numbers
    if re.search(r'\d', title):
        bonus += 6

    # Power words from niche
    pw = niche_dna.get("power_words", [])
    title_lower = title.lower()
    pw_hits = sum(1 for w in pw if w.lower() in title_lower)
    bonus += min(10, pw_hits * 4)

    # Strategy bonuses (some strategies perform better on YouTube)
    strategy_bonus = {
        "trending_hooks": 5,
        "curiosity_gaps": 8,
        "story_driven": 6,
        "fear_fomo": 7,
        "controversy_sparks": 4,
        "evergreen_magnets": 3,
    }
    bonus += strategy_bonus.get(idea.get("strategy", ""), 0)

    # Search potential
    sp = idea.get("search_potential", "medio").lower()
    if sp == "alto" or sp == "high":
        bonus += 8
    elif sp in ("medio", "medium"):
        bonus += 4

    # Emoji/special chars penalty (looks spammy)
    if any(ord(c) > 0x1F600 for c in title):
        bonus -= 5

    return min(100, max(0, (base_score + bonus)))


# ═══════════════════════════════════════════════════════════════
# Database Operations
# ═══════════════════════════════════════════════════════════════

def _ensure_ideas_table():
    """Create the ideas table if it doesn't exist."""
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS ideas (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id      TEXT NOT NULL,
                title           TEXT NOT NULL,
                hook            TEXT DEFAULT '',
                angle           TEXT DEFAULT '',
                why_viral       TEXT DEFAULT '',
                search_potential TEXT DEFAULT 'medium',
                strategy        TEXT DEFAULT '',
                virality_score  REAL DEFAULT 50,
                status          TEXT DEFAULT 'new',
                used            INTEGER DEFAULT 0,
                created_at      TEXT DEFAULT (datetime('now'))
            )
        """)


def _save_ideas(channel_id: str, ideas: list[dict]) -> int:
    """Save ideas to database. Returns number saved."""
    _ensure_ideas_table()
    saved = 0
    with get_db() as conn:
        for idea in ideas:
            # Skip duplicates (same title + channel)
            existing = conn.execute(
                "SELECT id FROM ideas WHERE channel_id = ? AND title = ?",
                (channel_id, idea.get("title", "")),
            ).fetchone()
            if existing:
                continue

            conn.execute(
                """INSERT INTO ideas
                   (channel_id, title, hook, angle, why_viral,
                    search_potential, strategy, virality_score)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    channel_id,
                    idea.get("title", "")[:200],
                    idea.get("hook", "")[:500],
                    idea.get("angle", "")[:500],
                    idea.get("why_viral", "")[:500],
                    idea.get("search_potential", "medium"),
                    idea.get("strategy", ""),
                    idea.get("virality_score", 50),
                ),
            )
            saved += 1
    return saved


def get_ideas(channel_id: str | None = None, strategy: str | None = None,
              unused_only: bool = False, limit: int = 50) -> list[dict]:
    """Retrieve ideas from database with optional filters."""
    _ensure_ideas_table()
    query = "SELECT * FROM ideas WHERE 1=1"
    params: list = []
    if channel_id:
        query += " AND channel_id = ?"
        params.append(channel_id)
    if strategy:
        query += " AND strategy = ?"
        params.append(strategy)
    if unused_only:
        query += " AND used = 0"
    query += " ORDER BY virality_score DESC LIMIT ?"
    params.append(limit)
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]


def mark_idea_used(idea_id: int) -> None:
    """Mark an idea as used (converted to video)."""
    _ensure_ideas_table()
    with get_db() as conn:
        conn.execute("UPDATE ideas SET used = 1, status = 'used' WHERE id = ?", (idea_id,))


def delete_idea(idea_id: int) -> None:
    """Delete a rejected idea."""
    _ensure_ideas_table()
    with get_db() as conn:
        conn.execute("DELETE FROM ideas WHERE id = ?", (idea_id,))


def get_idea_stats() -> dict:
    """Get stats about the idea pool."""
    _ensure_ideas_table()
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM ideas").fetchone()[0]
        unused = conn.execute("SELECT COUNT(*) FROM ideas WHERE used = 0").fetchone()[0]
        by_channel = [dict(r) for r in conn.execute("""
            SELECT channel_id, COUNT(*) as count,
                   AVG(virality_score) as avg_score,
                   COUNT(CASE WHEN used = 0 THEN 1 END) as available
            FROM ideas GROUP BY channel_id
        """).fetchall()]
        by_strategy = [dict(r) for r in conn.execute("""
            SELECT strategy, COUNT(*) as count,
                   AVG(virality_score) as avg_score
            FROM ideas GROUP BY strategy
        """).fetchall()]
        return {
            "total": total,
            "unused": unused,
            "by_channel": by_channel,
            "by_strategy": by_strategy,
        }


# ═══════════════════════════════════════════════════════════════
# Main Engine
# ═══════════════════════════════════════════════════════════════

def generate_ideas_for_channel(channel_id: str,
                               strategies: list[str] | None = None,
                               ideas_per_strategy: int = 5) -> dict:
    """
    Generate viral video ideas for a specific channel using all strategies.
    
    Args:
        channel_id: e.g., "impacto-mundial"
        strategies: list of strategy keys, or None for all 6
        ideas_per_strategy: number of ideas per strategy (default 5)
    
    Returns:
        dict with generated ideas grouped by strategy + stats
    """
    if channel_id not in NICHE_DNA:
        raise ValueError(f"Unknown channel: {channel_id}. Valid: {list(NICHE_DNA.keys())}")

    dna = NICHE_DNA[channel_id]
    lang = dna["lang"]
    lang_label = "español" if lang == "es" else "English"

    if strategies is None:
        strategies = list(STRATEGIES.keys())
    else:
        strategies = [s for s in strategies if s in STRATEGIES]

    logger.info(f"💡 Generating ideas for '{dna['name']}' — {len(strategies)} strategies x {ideas_per_strategy} ideas")

    all_ideas: list[dict] = []
    results_by_strategy: dict[str, list[dict]] = {}

    for strat_key in strategies:
        strat = STRATEGIES[strat_key]
        logger.info(f"   📌 Strategy: {strat['name_es']}...")

        prompt = strat["prompt_template"].format(
            count=ideas_per_strategy,
            niche=dna["name"] + " — " + ", ".join(dna["core_themes"][:5]),
            lang_label=lang_label,
            themes=", ".join(dna["core_themes"]),
            competitors=", ".join(dna.get("competitor_channels", [])),
        )

        raw_response = _call_gemini(prompt)
        ideas = _parse_ideas_json(raw_response)

        # Enhance scores
        for idea in ideas:
            idea["strategy"] = strat_key
            idea["channel_id"] = channel_id
            idea["virality_score"] = _enhance_score(idea, dna)

        # Sort by score
        ideas.sort(key=lambda x: x.get("virality_score", 0), reverse=True)

        results_by_strategy[strat_key] = ideas
        all_ideas.extend(ideas)

        # Rate limit: ~2s between calls to stay within Gemini free tier
        time.sleep(2)

    # Save to database
    saved = _save_ideas(channel_id, all_ideas)

    # Sort all by virality score
    all_ideas.sort(key=lambda x: x.get("virality_score", 0), reverse=True)

    logger.info(f"   ✅ Generated {len(all_ideas)} ideas, saved {saved} new to database")

    return {
        "channel_id": channel_id,
        "channel_name": dna["name"],
        "total_generated": len(all_ideas),
        "new_saved": saved,
        "ideas": all_ideas,
        "by_strategy": {
            k: {
                "name": STRATEGIES[k]["name_es"],
                "description": STRATEGIES[k]["description"],
                "ideas": v,
            }
            for k, v in results_by_strategy.items()
        },
        "top_5": all_ideas[:5],
    }


def generate_ideas_all_channels(ideas_per_strategy: int = 3) -> dict:
    """Generate ideas for ALL 6 channels."""
    logger.info("🌐 Generating ideas for ALL channels...")
    results = {}
    for channel_id in NICHE_DNA:
        try:
            result = generate_ideas_for_channel(
                channel_id, ideas_per_strategy=ideas_per_strategy
            )
            results[channel_id] = result
            logger.info(f"   ✅ {result['channel_name']}: {result['total_generated']} ideas")
        except Exception as exc:
            logger.error(f"   ❌ {channel_id}: {exc}")
            results[channel_id] = {"error": str(exc)}
        time.sleep(3)  # Extra delay between channels

    total = sum(r.get("total_generated", 0) for r in results.values() if isinstance(r, dict))
    logger.info(f"🏁 Done! {total} ideas generated across {len(results)} channels")
    return results


def get_best_idea(channel_id: str) -> dict | None:
    """Get the highest-scoring unused idea for a channel."""
    ideas = get_ideas(channel_id=channel_id, unused_only=True, limit=1)
    return ideas[0] if ideas else None
