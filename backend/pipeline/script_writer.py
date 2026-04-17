"""
YouTube Automation Pro — Script Writer
Generates optimized video scripts per channel niche with proper structure,
retention hooks, B-roll markers, and anti-AI-detection patterns.
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config import env, CHANNEL_DIRS
from ..database import log_api_usage, log_pipeline_step, update_video
from .humanizer import humanize_text, humanize_title

logger = logging.getLogger("script-writer")


# ═══════════════════════════════════════════════════════════════
# Channel-Specific Prompt Templates
# ═══════════════════════════════════════════════════════════════

CHANNEL_PROMPTS = {
    "impacto-mundial": {
        "system": (
            "Eres un guionista experto de documentales de misterio en español. "
            "Tu estilo combina narrativa de investigación periodística con tensión "
            "cinematográfica. Escribes como si estuvieras revelando un secreto que "
            "alguien no quiere que se sepa. Usas frases cortas y directas. "
            "Nunca dices 'hola' ni te presentas. Empiezas directo con el dato más impactante."
        ),
        "tone_instructions": (
            "Tono: misterioso, tenso, revelador. "
            "Usa pausas dramáticas marcadas con '...' "
            "Vocabulario: desclasificado, prohibido, oculto, revelación, expediente, archivos secretos. "
            "Frases de máximo 12 palabras. Alterna frases cortas (3-5 palabras) con más largas."
        ),
        "broll_examples": [
            "aerial view abandoned city ruins",
            "classified documents stack closeup",
            "ancient map mysterious markings",
            "satellite imagery restricted area",
            "dark corridor underground facility",
        ],
    },
    "mentes-rotas": {
        "system": (
            "Eres un guionista de documentales de true crime en español. "
            "Narras como un detective experimentado revisando un caso frío. "
            "Tu tono es serio, investigativo y nunca sensacionalista. "
            "Presentas hechos con precisión cronológica. "
            "Generas tensión revelando información progresivamente."
        ),
        "tone_instructions": (
            "Tono: investigativo, oscuro, suspense constante. "
            "Estructura cronológica del caso. Intercala datos con preguntas retóricas. "
            "Vocabulario: expediente, escena del crimen, evidencia, perfil criminal, interrogatorio. "
            "Incluye citas textuales (inventadas pero realistas) de testigos o investigadores."
        ),
        "broll_examples": [
            "police investigation room evidence board",
            "crime scene tape dark night",
            "old newspaper clippings crime",
            "empty interrogation room spotlight",
            "forensic laboratory analysis",
        ],
    },
    "el-loco-de-la-ia": {
        "system": (
            "Eres un experto en IA y tecnología que hace tutoriales prácticos en español. "
            "Tu estilo es directo, entusiasta y orientado a resultados. "
            "Siempre muestras el valor práctico y el ahorro de tiempo. "
            "Hablas como un amigo que acaba de descubrir algo increíble y no puede "
            "esperar para contártelo."
        ),
        "tone_instructions": (
            "Tono: entusiasta, directo, práctico. "
            "Vocabulario: herramienta, automatizar, gratis, minutos, resultados, paso a paso. "
            "Incluye cifras concretas de ahorro de tiempo/dinero. "
            "Cada punto debe tener un beneficio inmediato y tangible."
        ),
        "broll_examples": [
            "modern software interface screen recording",
            "person working laptop futuristic dashboard",
            "growth chart analytics positive",
            "code editor programming clean",
            "money savings financial chart",
        ],
    },
    "mind-warp": {
        "system": (
            "You are an expert psychology scriptwriter for YouTube documentaries. "
            "You combine scientific rigor with storytelling that makes complex concepts "
            "accessible and deeply unsettling. You cite real studies and experiments. "
            "You make the viewer question their own behavior and perception."
        ),
        "tone_instructions": (
            "Tone: intellectual yet accessible, thought-provoking, slightly unsettling. "
            "Use real study references (author names, years, universities). "
            "Vocabulary: cognitive bias, neural pathways, subconscious, manipulation, perception. "
            "End each section with a disturbing implication for daily life."
        ),
        "broll_examples": [
            "human brain neural connections glowing",
            "psychology experiment laboratory",
            "person looking mirror contemplative",
            "crowd people manipulation concept",
            "brain scan MRI colorful",
        ],
    },
    "wealth-files": {
        "system": (
            "You are a financial documentary scriptwriter who reveals the hidden mechanics "
            "of extreme wealth. You combine investigative journalism with aspirational storytelling. "
            "You use specific numbers, dates, and names. You never use generic advice — "
            "every point is backed by a concrete example from a real billionaire or company."
        ),
        "tone_instructions": (
            "Tone: authoritative, revealing, data-driven, aspirational but realistic. "
            "Use specific dollar amounts, percentages, and timelines. "
            "Vocabulary: portfolio, leverage, compound, equity, net worth, acquisition. "
            "Contrast conventional wisdom with what wealthy people actually do."
        ),
        "broll_examples": [
            "luxury penthouse city view night",
            "stock market trading floor",
            "private jet interior golden light",
            "financial charts growth trending",
            "mansion aerial view estate",
        ],
    },
    "dark-science": {
        "system": (
            "You are a science documentary scriptwriter specializing in making complex "
            "scientific topics both accessible and terrifying. You explain quantum physics, "
            "deep ocean mysteries, and space phenomena in a way that fills people with "
            "awe and existential dread simultaneously. You use analogies perfectly."
        ),
        "tone_instructions": (
            "Tone: documentary, awe-inspiring, slightly terrifying. "
            "Use precise scientific terminology but always explain it simply. "
            "Vocabulary: cosmological, quantum, phenomenon, anomaly, paradox, singularity. "
            "Include scale comparisons (e.g., 'this object is larger than 1000 Earths')."
        ),
        "broll_examples": [
            "deep space nebula colorful",
            "deep ocean mysterious creature bioluminescent",
            "particle physics laboratory CERN",
            "earth from space atmospheric glow",
            "black hole artistic visualization",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════
# Script Structure Template
# ═══════════════════════════════════════════════════════════════

def _build_prompt(topic: str, channel: dict) -> str:
    """Build the complete prompt for script generation."""
    channel_id = channel["channel_id"]
    language = channel.get("language", "es")
    prompts = CHANNEL_PROMPTS.get(channel_id, CHANNEL_PROMPTS["mind-warp"])
    # Force videos to be between 5 and 15 minutes
    dur_min = max(5, channel.get("duration_min", 5))
    dur_max = min(15, channel.get("duration_max", 15))
    # TTS reading speed is ~150 words per minute
    word_count_min = dur_min * 150
    word_count_max = dur_max * 150

    lang_label = "español" if language == "es" else "English"

    return f"""{prompts['system']}

{prompts['tone_instructions']}

TOPIC: {topic}

Generate a HIGHLY DETAILED, SPECTACULAR YouTube script in {lang_label} with these EXACT sections:

## HOOK (first 10 seconds, max 30 words)
- Start with the most shocking fact or moment. NO greetings.
- One single powerful sentence that makes it impossible not to keep watching.

## PROMISE (10-30 seconds)
- What the viewer will learn/discover
- Why it matters to them personally
- Why they haven't heard this before
- Use: "Al final de este video entenderás por qué..." / "By the end of this video you'll understand why..."

## CONTENT (main body — 8-12 extensive sections)
Each section MUST be extremely detailed and well-researched. This is a DOCUMENTARY-style video.
- A section title (narrative, not numbered)
- Deep, elaborate content with facts, data, storytelling, and vivid descriptions
- A retention hook at the end of each section: unanswered question, partial reveal, or "pero hay algo que no te he contado..."
- B-roll indicators between brackets, at least 2 per section, like: [B-ROLL: "query for stock footage"]
  Use these B-roll style queries: {', '.join(prompts['broll_examples'][:3])}

## INTEGRATED CTA (at ~85% of the video)
- Naturally woven into the narrative, NOT a separate section
- Example: "Si quieres saber cómo termina esta historia, asegúrate de estar suscrito"

## CLOSING (last 45 seconds)
- Resolve the main narrative tension
- Reflective thought that lingers
- Natural bridge to subscribe and next video
- NEVER use: "In conclusion", "As we've seen", "I hope you enjoyed"

IMPORTANT RULES:
1. STRICT WORD COUNT: Minimum {word_count_min} words, maximum {word_count_max} words. The script MUST be long enough for a {dur_min}-{dur_max} minute video.
2. Expand heavily on every point. Use rich vocabulary and spectacular descriptions.
3. Mix very short sentences (3-5 words) with longer ones for rhythm.
4. Include at least 20 [B-ROLL: "..."] markers throughout the script.
5. Use transition phrases: "But here's what nobody mentions", "And then something happened that changed everything"
6. Add a pattern interrupt every 8-12 seconds of narration (question, shock data point, contrast, or visual switch cue).
7. In the first 30 seconds, explicitly answer: "what does the viewer gain by staying?"
8. Write naturally — avoid AI patterns like "delve", "it's important to note", "in this rapidly evolving"
9. B-ROLL markers must be specific and contextual (people/places/objects/events), avoid generic placeholders like "cinematic footage" or "dramatic scene".
10. Keep visual continuity: each section should include B-ROLL terms directly tied to that section's facts, not repeated generic queries.

Also generate at the end:
## TITLES (5 options, max 60 characters each)
## SEO DESCRIPTION (400 characters max)
## TAGS (15 tags, comma-separated)
## SHORT VERSION (60-second version of the best hook + key insight, max 150 words)
"""


# ═══════════════════════════════════════════════════════════════
# Script Generation
# ═══════════════════════════════════════════════════════════════

def generate_script(topic: str, channel: dict, video_id: int | None = None) -> dict:
    """
    Generate a complete video script for a channel.
    Implements controlled fallback chain: Gemini → Local template.
    Hides internal errors per SCRIPT_HIDE_ERRORS config.
    Returns dict with: title, script, short_script, seo_description, tags, broll_markers
    """
    from ..config import SCRIPT_CONFIG
    
    channel_id = channel["channel_id"]
    language = channel.get("language", "es")

    logger.info(f"📝 Generating script for '{channel['name']}': {topic}")

    prompt = _build_prompt(topic, channel)
    script_text = ""
    title = topic
    used_fallback = False

    # Try Gemini API (unless free-first local mode is requested)
    script_provider = env("SCRIPT_PROVIDER", "auto").strip().lower()
    gemini_key = env("GEMINI_API_KEY")
    use_gemini = script_provider in {"auto", "gemini"} and bool(gemini_key)
    
    if use_gemini:
        for attempt in range(1, SCRIPT_CONFIG["max_retries"] + 1):
            try:
                from google import genai
                client = genai.Client(api_key=gemini_key)
                response = client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=prompt,
                )
                ai_text = (response.text or "").strip()
                if ai_text and len(ai_text) > 500:
                    script_text = ai_text
                    # Extract best title from generated titles
                    title = _extract_best_title(ai_text, topic)
                    log_api_usage("gemini", "generate_content",
                                  chars=len(prompt) + len(ai_text))
                    logger.info(f"   ✅ Script generated via Gemini ({len(ai_text)} chars)")
                    break
                else:
                    logger.debug(f"   Gemini response too short ({len(ai_text)} chars), retrying...")
            except Exception as exc:
                error_detail = str(exc) if not SCRIPT_CONFIG["hide_errors"] else "API call failed"
                logger.warning(f"   ⚠️ Gemini error (attempt {attempt}): {error_detail}")
                if attempt < SCRIPT_CONFIG["max_retries"]:
                    time.sleep(2 * attempt)  # Exponential backoff
    elif script_provider == "local":
        logger.info("   Script provider set to local. Skipping Gemini.")

    # Fallback: high-quality template
    if not script_text:
        logger.info("   Using local template fallback (no Gemini response)")
        title, script_text = _local_fallback(topic, channel)
        used_fallback = True

    # Humanize script + title for final output quality
    script_text = humanize_text(script_text, channel_id)
    title = humanize_title(title, channel_id)

    # Extract B-roll markers
    broll_markers = re.findall(r'\[B-ROLL:\s*"([^"]+)"\]', script_text)

    # Extract short version
    short_script = _extract_short(script_text)

    # Extract SEO metadata
    seo_desc = _extract_section(script_text, "SEO DESCRIPTION", 400)
    tags = _extract_section(script_text, "TAGS", 500)

    # Save to file
    channel_dir = CHANNEL_DIRS.get(channel_id)
    if channel_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^a-z0-9\s-]", "", topic.lower())[:60].replace(" ", "-")
        script_path = channel_dir / "scripts" / f"{timestamp}_{slug}.txt"
        script_path.write_text(script_text, encoding="utf-8")
    else:
        script_path = Path("script.txt")

    # Update video record if we have one
    if video_id:
        update_video(video_id, {
            "title": title,
            "script_text": script_text,
            "script_path": str(script_path),
            "status": "script_ready",
            "script_source": "fallback" if used_fallback else "gemini",
        })
        source_label = "fallback template" if used_fallback else "Gemini API"
        log_pipeline_step(channel.get("id"), video_id, "script_writer", "ok",
                          f"Script generated from {source_label}: {len(script_text)} chars")

    return {
        "title": title,
        "script": script_text,
        "script_path": str(script_path),
        "short_script": short_script,
        "seo_description": seo_desc,
        "tags": tags,
        "broll_markers": broll_markers,
        "word_count": len(script_text.split()),
        "source": "fallback" if used_fallback else "gemini",
    }


def _extract_best_title(script: str, fallback: str) -> str:
    """Extract the best title from the TITLES section of the script."""
    lines = script.split("\n")
    in_titles = False
    titles = []
    for line in lines:
        if "## TITLES" in line.upper() or "## TÍTULOS" in line.upper():
            in_titles = True
            continue
        if in_titles:
            if line.startswith("##"):
                break
            clean = re.sub(r"^\d+[\.\)]\s*", "", line.strip()).strip('"\'')
            if clean and len(clean) > 10:
                titles.append(clean)

    if not titles:
        # Try to extract from first line
        first = lines[0].strip().lstrip("#").strip()
        if first and len(first) > 10:
            return first[:100]
        return fallback

    # Score titles: prefer 45-60 chars, with numbers, power words
    def score(t: str) -> float:
        s = 0.0
        if 45 <= len(t) <= 60:
            s += 30
        elif 30 <= len(t) <= 70:
            s += 15
        if any(c.isdigit() for c in t):
            s += 20
        power_words = {"secret", "hidden", "nobody", "truth", "shocking",
                       "secreto", "oculto", "nadie", "verdad", "impactante",
                       "never", "nunca", "prohibido", "forbidden"}
        for pw in power_words:
            if pw in t.lower():
                s += 10
                break
        return s

    titles.sort(key=score, reverse=True)
    return titles[0][:100]


def _extract_short(script: str) -> str:
    """Extract or generate 60-second Short version."""
    # Look for SHORT VERSION section
    match = re.search(r"##\s*SHORT\s*VERSION(.*?)(?=##|$)", script, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()[:800]

    # Fallback: take the hook + first content section
    lines = script.split("\n")
    short_lines = []
    word_count = 0
    for line in lines:
        if word_count > 200:  # ~90 seconds at speaking pace
            break
        if line.startswith("##"):
            continue
        short_lines.append(line)
        word_count += len(line.split())

    return "\n".join(short_lines)[:800]


def _extract_section(script: str, section_name: str, max_chars: int) -> str:
    """Extract a named section from the script."""
    pattern = rf"##\s*{re.escape(section_name)}(.*?)(?=##|$)"
    match = re.search(pattern, script, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()[:max_chars]
    return ""


def _topic_keywords(topic: str, language: str, limit: int = 6) -> list[str]:
    """Extract useful keywords from topic text."""
    stop_es = {
        "de", "la", "el", "los", "las", "un", "una", "y", "o", "que", "en", "del", "al",
        "por", "para", "con", "sobre", "lo", "se", "su", "sus", "como", "más", "menos",
    }
    stop_en = {
        "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "about",
        "from", "is", "are", "was", "were", "be", "this", "that", "these", "those",
    }
    stops = stop_es if language == "es" else stop_en
    words = re.findall(r"[a-zA-ZÀ-ÿ0-9]{3,}", topic.lower())
    unique: list[str] = []
    for word in words:
        if word in stops:
            continue
        if word not in unique:
            unique.append(word)
        if len(unique) >= limit:
            break
    if unique:
        return unique
    return [topic.split()[0].lower()] if topic.split() else ["misterio"]


def _build_fallback_broll_queries(topic: str, channel: dict, language: str) -> list[str]:
    """Create topic-aware B-roll queries for local fallback mode."""
    channel_id = channel.get("channel_id", "")
    keywords = _topic_keywords(topic, language, limit=5)
    base = [
        f"{topic} documentary cinematic",
        f"{topic} archive footage",
        f"{topic} dramatic close up",
    ]
    by_channel = {
        "impacto-mundial": ["classified documents", "mysterious tunnel", "satellite map night"],
        "mentes-rotas": ["crime scene board", "forensic evidence table", "interrogation room light"],
        "el-loco-de-la-ia": ["ai interface animation", "code screen closeup", "data center servers"],
        "mind-warp": ["brain scan animation", "psychology lab", "city crowd slow motion"],
        "wealth-files": ["stock market screen", "luxury skyline", "business deal handshake"],
        "dark-science": ["deep space nebula", "particle accelerator", "deep ocean bioluminescent"],
    }.get(channel_id, ["cinematic atmosphere", "dramatic portrait", "data visualization"])
    return base + by_channel + [f"{k} cinematic broll" for k in keywords]


def _local_fallback(topic: str, channel: dict) -> tuple[str, str]:
    """High-quality local fallback when AI is unavailable."""
    language = channel.get("language", "es")
    broll = _build_fallback_broll_queries(topic, channel, language)
    q1, q2, q3, q4, q5, q6 = (broll + broll[:6])[:6]
    q7, q8, q9, q10 = (broll + broll[:10])[6:10]
    key_terms = ", ".join(_topic_keywords(topic, language, limit=4))

    if language == "es":
        title = f"{topic}: Lo que nadie te ha contado"
        script = f"""## HOOK
{topic}. Lo que se descubrió detrás de este tema no era un rumor. Era un patrón real.

[B-ROLL: "{q1}"]

## PROMISE
En este video vas a entender qué pasó, quién se benefició y por qué casi nadie te lo explica con contexto.
Vamos a conectar fechas, decisiones y consecuencias para que veas la historia completa.

## SECCIÓN 1 — El origen
Todo empezó mucho antes de lo que imaginas. Al principio parecía un hecho aislado, una coincidencia más.
Pero cuando revisas la cronología, aparecen señales repetidas: mismos actores, mismas decisiones, mismo silencio.
Eso no ocurre por accidente.

[B-ROLL: "{q2}"]

La razón principal era estratégica: si el contexto se hacía público, varias narrativas oficiales perdían credibilidad.
Y cuando una narrativa se rompe, también se rompe el control.

[B-ROLL: "{q3}"]

Pero hay una pieza clave que casi siempre se omite...

## SECCIÓN 2 — La revelación
Cuando comparas documentos, testimonios y datos abiertos, se ve una correlación difícil de ignorar.
No hablamos de una teoría suelta: hablamos de una secuencia verificable con impactos medibles.

[B-ROLL: "{q4}"]

El punto crítico no es solo lo que pasó, sino cómo se encadenó.
Cada evento preparó el siguiente, y cada decisión tuvo una consecuencia concreta sobre la gente común.

## SECCIÓN 3 — Lo que no encaja
Aquí es donde todo se vuelve incómodo: hay inconsistencias que llevan años frente a nosotros.
Versiones cambiadas, informes incompletos y detalles que desaparecen justo cuando deberían aclarar dudas.

[B-ROLL: "{q5}"]

Si unes esas piezas, la lectura cambia por completo: no era confusión, era diseño.

## SECCIÓN 4 — Impacto real en tu día a día
Puede parecer una historia lejana, pero influye en lo que consumes, en lo que temes y en lo que consideras posible.
Las narrativas moldean decisiones personales, políticas y económicas.
Y cuando la narrativa parte de una base débil, el coste lo paga siempre la audiencia.

[B-ROLL: "{q6}"]
[B-ROLL: "{q7}"]

## SECCIÓN 5 — Qué mirar a partir de ahora
A partir de hoy, no te quedes con titulares. Mira fuentes primarias, compara fechas y busca incentivos.
Cuando analizas quién gana con una versión concreta, entiendes por qué ciertas preguntas nunca llegan a portada.
Si quieres que destripemos la segunda parte con pruebas nuevas y casos comparables, suscríbete ahora porque lo que sigue es todavía más fuerte.
[B-ROLL: "{q8}"]
[B-ROLL: "{q9}"]
[B-ROLL: "{q10}"]

## CTA INTEGRADO
Si este formato te aporta claridad, suscríbete y activa la campana para no perderte el siguiente episodio.

## CIERRE
La próxima vez que escuches sobre {topic}, recuerda esto: no gana quien habla más alto, gana quien conecta mejor las pruebas.
Y ahora tú ya tienes el mapa completo para detectar cuándo te están contando solo media verdad.

## TITLES
1) {topic}: La verdad que nadie se atreve a contar
2) Lo que descubrieron sobre {topic} te dejará sin palabras
3) {topic}: El secreto que estaba frente a tus ojos
4) {topic}: cronología real y pruebas clave
5) {topic}: cómo se construyó la narrativa oficial

## SEO DESCRIPTION
Análisis documental de {topic} con cronología, pruebas y contexto real. Descubre qué no encaja, quién gana con cada versión y cómo interpretar los datos sin caer en titulares vacíos.

## TAGS
{topic}, {key_terms}, misterios, revelaciones, documentales, verdad oculta, investigación, datos reales, cronología, análisis

## SHORT VERSION
{topic} no fue un accidente aislado. Al revisar cronología, documentos y consecuencias, aparece un patrón que casi nunca se explica completo.
Si entiendes quién gana con cada narrativa, entiendes por qué ciertas preguntas desaparecen.
"""
    else:
        title = f"{topic}: What Nobody Tells You"
        script = f"""## HOOK
{topic}. What surfaced around this story wasn't noise. It was a repeatable pattern.

[B-ROLL: "{q1}"]

## PROMISE
In the next minutes, you'll see what happened, why it mattered, and why most summaries leave out the uncomfortable part.

## SECTION 1 — The Origin
This started earlier than most timelines admit. At first, it looked isolated.
Then the same decisions, same actors, and same blind spots began to repeat.

[B-ROLL: "{q2}"]

That repetition is the signal. Not the noise.
And it points to coordination, not coincidence.

[B-ROLL: "{q3}"]

But one critical piece is still missing...

## SECTION 2 — The Revelation
When you align documents, witness accounts, and public datasets, a stronger picture emerges.
Not a dramatic guess. A traceable chain.

[B-ROLL: "{q4}"]

And that chain explains outcomes that once looked random.

## SECTION 3 — What Doesn't Fit
Contradictory reports, edited timelines, and missing context are not minor details.
They're the architecture of how narratives are controlled.

[B-ROLL: "{q5}"]

## SECTION 4 — Why This Affects You
Stories shape behavior, policy, and money flows. That's why this matters beyond curiosity.
If the baseline story is weak, the real cost lands on the audience.

[B-ROLL: "{q6}"]

## SECTION 5 — What To Watch Next
Track primary sources, compare dates, and always ask who benefits from the official version.
If you want part two with direct case comparisons, subscribe now.

## INTEGRATED CTA
If you want to understand more about topics like this, there's a simple way: subscribe and hit the bell. That way you won't miss part two.

## CLOSING
The next time you hear about {topic}, remember what you learned today. Because now you know something most people don't.

## TITLES
1) {topic}: The Truth Nobody Dares to Tell
2) What They Discovered About {topic} Will Leave You Speechless
3) {topic}: The Secret Hiding in Plain Sight
4) {topic}: timeline, evidence, and hidden links
5) {topic}: what the official story leaves out

## SEO DESCRIPTION
Documentary-style breakdown of {topic} with timeline context, evidence mapping, and key contradictions most summaries ignore.

## TAGS
{topic}, {key_terms}, mysteries, revelations, documentary, hidden truth, investigation, real data, timeline, analysis

## SHORT VERSION
{topic} looks simple until you line up dates, evidence, and who benefits from each version.
Once you see the pattern, you can't unsee it.
"""
    return title, script
