import json
import math
import re


TYPE_WEIGHTS = {
    "podcast": [0.20, 0.15, 0.25, 0.20, 0.05, 0.05, 0.10],
    "concurso": [0.30, 0.10, 0.15, 0.15, 0.15, 0.10, 0.05],
    "stream": [0.25, 0.10, 0.15, 0.10, 0.20, 0.10, 0.10],
}


SEMANTIC_REVELATION = [
    "nunca", "jamas", "por primera vez", "nadie sabe", "secreto", "te lo juro",
    "no me lo creo", "imposible", "flipante", "alucinante", "increible", "brutal",
    "no puede ser", "en serio", "de verdad",
]

SEMANTIC_COLLOQUIAL = [
    "tio", "tia", "chaval", "crack", "maquina", "bro", "flipar", "petarlo",
    "reventar", "locura", "salvaje",
]

BORING_FILLERS = [
    "basicamente", "o sea", "es que", "pues nada", "como os decia", "vamos a ver", "bueno",
]

EXTERNAL_REFERENCES = [
    "como te decia", "antes hablamos", "lo que dijiste", "volviendo a", "continuando",
    "como mencione", "al principio", "al final", "en el capitulo", "lo que sigue",
    "ahora si", "pues como iba diciendo",
]

SELF_PRESENTATION = [
    "soy", "te cuento", "imaginate", "resulta que", "os voy a contar", "fijaos",
    "mirad", "escuchad", "hoy", "ayer", "el otro dia", "una vez",
]


def _normalize_text(text):
    text = (text or "").lower().strip()
    return text.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")


def _classify_video(title, transcript_partial):
    text = _normalize_text(f"{title or ''} {transcript_partial or ''}")

    podcast_hits = sum(k in text for k in ["podcast", "entrevista", "debate", "charla"])
    contest_hits = sum(k in text for k in ["reto", "desafio", "concurso", "ibai", "mrbeast"])
    stream_hits = sum(k in text for k in ["stream", "directo", "gaming", "chat", "reaccion"])

    scores = {
        "podcast": podcast_hits,
        "concurso": contest_hits,
        "stream": stream_hits,
    }
    detected = max(scores, key=scores.get)
    confidence = 0.7 if scores[detected] > 0 else 0.5

    return {
        "tipo": detected,
        "pesos": TYPE_WEIGHTS[detected],
        "confianza": confidence,
    }


def _detector_emocion(segment_text):
    low = _normalize_text(segment_text)
    score = 35
    score += min(low.count("!") * 8, 24)
    score += min(sum(1 for p in ["wow", "brutal", "increible", "locura", "madre mia"] if p in low) * 16, 48)
    if re.search(r"\b(jaj|jaja|risas|grita|grito|screaming)\b", low):
        score += 20
    return min(score, 100)


def _detector_silencio_dramatico(segments, start, end):
    segs = [s for s in segments if s.get("start", 0) >= start and s.get("end", 0) <= end]
    if len(segs) < 2:
        return 0

    score = 0
    pauses = 0
    for idx in range(len(segs) - 1):
        a = segs[idx]
        b = segs[idx + 1]
        pause = float(b.get("start", 0)) - float(a.get("end", 0))
        if 0.8 <= pause <= 3.0:
            pauses += 1
            dur = max(float(b.get("end", 0)) - float(b.get("start", 0)), 0.1)
            speed = len((b.get("text") or "").split()) / dur
            score += 30 if speed > 3.5 else 15

    return min(score * (1 + pauses * 0.2), 100)


def _detector_semantico(text):
    low = _normalize_text(text)
    score = 12

    hits_a = sum(1 for p in SEMANTIC_REVELATION if p in low)
    score += min(hits_a * 20, 60)

    numeros = re.findall(
        r"\b\d+(?:[.,]\d+)?\s*(?:mil|millon|millones|€|euros|%|veces|anos|dias|horas|segundos|metros|kilos|personas)\b",
        low,
    )
    score += min(len(numeros) * 15, 30)

    score += min(text.count("?") * 10, 20)

    hits_d = sum(1 for p in SEMANTIC_COLLOQUIAL if p in low)
    score += min(hits_d * 5, 20)

    hits_boring = sum(1 for p in BORING_FILLERS if p in low)
    score -= hits_boring * 8

    return max(min(score, 100), 0)


def _detector_narrativa(text, tipo_video):
    low = _normalize_text(text)

    # Baseline heuristics that guarantee deterministic behavior when no LLM is configured.
    inicio = 16 if re.search(r"\b(hoy|imaginate|te cuento|nunca|por primera vez|pregunta)\b", low) else 10
    desarrollo = min(20, 8 + min(len(text.split()) / 12, 12))
    cierre = 16 if re.search(r"\b(asi que|por eso|en resumen|resultado|finalmente|total)\b", low) else 10
    autonomia = 20
    if any(ref in low for ref in EXTERNAL_REFERENCES):
        autonomia -= 10
    if re.search(r"^(el|ella|ellos|eso|esto|ese|esa|aquello)\b", low):
        autonomia -= 8
    retencion = min(20, 8 + _detector_semantico(text) / 10)

    # Optional LLM refinement via Ollama, best-effort only.
    if _is_true_env("USE_OLLAMA_NARRATIVE", default=False):
        try:
            import ollama

            prompt = (
                "Analiza este fragmento de video en espanol y devuelve JSON puro con: "
                "inicio, desarrollo, cierre, autonomia, retencion, razon (todos 0-20 salvo razon). "
                f"Tipo: {tipo_video}. Texto: {text}"
            )
            resp = ollama.chat(
                model="mistral",
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.2},
            )
            raw = resp["message"]["content"]
            data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
            inicio = float(data.get("inicio", inicio))
            desarrollo = float(data.get("desarrollo", desarrollo))
            cierre = float(data.get("cierre", cierre))
            autonomia = float(data.get("autonomia", autonomia))
            retencion = float(data.get("retencion", retencion))
        except Exception:
            pass

    if autonomia < 12:
        return 0

    return max(0, min(100, inicio + desarrollo + cierre + autonomia + retencion))


def _detector_visual(start, end):
    # Lightweight placeholder: without frame data, prefer a neutral value.
    # Keeps detector architecture complete without adding heavy mandatory deps.
    dur = max(end - start, 1.0)
    baseline = 50 + min(30, dur / 2)
    return float(min(100, baseline))


def _detector_ritmo(segments, start, end):
    segs = [s for s in segments if s.get("start", 0) >= start and s.get("end", 0) <= end]
    if not segs:
        return 0

    speeds = []
    for seg in segs:
        dur = float(seg.get("end", 0)) - float(seg.get("start", 0))
        if dur > 0.1:
            speeds.append(len((seg.get("text") or "").split()) / dur)

    if not speeds:
        return 0

    mean_speed = sum(speeds) / len(speeds)
    std_speed = math.sqrt(sum((x - mean_speed) ** 2 for x in speeds) / len(speeds))

    if 2.5 <= mean_speed <= 4.5:
        score_speed = 70
    elif 1.5 <= mean_speed < 2.5:
        score_speed = 50
    elif mean_speed > 4.5:
        score_speed = 58
    else:
        score_speed = 25

    score_var = min(std_speed * 15, 40)
    return min(score_speed + score_var, 100)


def _detector_contexto_autonomo(text):
    low = _normalize_text(text)
    score = 100

    for ref in EXTERNAL_REFERENCES:
        if ref in low:
            score -= 25

    first_words = low.split()[:5]
    if first_words and first_words[0] in {"el", "ella", "ellos", "eso", "esto", "ese", "esa", "aquello"}:
        score -= 30

    if any(ap in low for ap in SELF_PRESENTATION):
        score += 10

    return max(min(score, 100), 0)


def _calc_final_score(detector_scores, weights):
    d1, d2, d3, d4, d5, d6, d7 = detector_scores

    if d4 == 0:
        return 0
    if d3 < 10:
        return 0
    if d6 < 5:
        return 0

    score = sum(s * w for s, w in zip(detector_scores, weights))

    if d1 > 70 and d4 > 70:
        score *= 1.15
    if d2 > 60 and d3 > 60:
        score *= 1.10
    if d7 > 80 and d3 > 70 and d6 > 60:
        score *= 1.12

    return min(score, 100)


def _decide_duration(start, end, score, tipo_video):
    natural = max(end - start, 1.0)

    if tipo_video == "concurso":
        if natural <= 20:
            return natural
        if score > 85:
            return min(natural, 45)
        return min(natural, 30)

    if tipo_video == "podcast":
        if score > 85:
            return min(natural, 55)
        if score > 72:
            return min(natural, 40)
        return min(natural, 32)

    if tipo_video == "stream":
        if score > 85:
            return min(natural, 60)
        return min(natural, 40)

    return min(natural, 60)


def _remove_overlaps(candidates, min_gap=30.0):
    if not candidates:
        return []

    ranked = sorted(candidates, key=lambda x: x["score"], reverse=True)
    approved = []

    for c in ranked:
        overlap = False
        for a in approved:
            if c["start"] < a["end"] + min_gap and c["end"] > a["start"] - min_gap:
                overlap = True
                break
        if not overlap:
            approved.append(c)

    return approved


def _is_true_env(name, default=False):
    raw = str(__import__("os").getenv(name, "1" if default else "0")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def detect_peak_moments(transcript_segments, num_clips=5, title="", video_type="auto"):
    if not transcript_segments:
        return []

    ordered = sorted(transcript_segments, key=lambda s: float(s.get("start", 0)))
    transcript_text = " ".join((s.get("text") or "") for s in ordered)

    if video_type == "auto":
        c = _classify_video(title, transcript_text[:600])
    else:
        chosen = video_type if video_type in TYPE_WEIGHTS else "podcast"
        c = {"tipo": chosen, "pesos": TYPE_WEIGHTS[chosen], "confianza": 0.8}

    tipo = c["tipo"]
    pesos = c["pesos"]

    # Windowed analysis tuned for multiple usable clips.
    duration_total = max(float(s.get("end", 0)) for s in ordered)
    window = 50.0
    step = 12.0
    threshold = 72.0
    t = 0.0
    candidates = []
    evaluated = []

    while t < max(0.0, duration_total - 20.0):
        t_end = min(t + window, duration_total)
        segs_window = [s for s in ordered if float(s.get("start", 0)) >= t and float(s.get("end", 0)) <= t_end]
        if not segs_window:
            t += step
            continue

        text = " ".join((s.get("text") or "") for s in segs_window).strip()
        if not text:
            t += step
            continue

        d1 = _detector_emocion(text)
        d2 = _detector_silencio_dramatico(ordered, t, t_end)
        d3 = _detector_semantico(text)
        d4 = _detector_narrativa(text, tipo)
        d5 = _detector_visual(t, t_end)
        d6 = _detector_ritmo(ordered, t, t_end)
        d7 = _detector_contexto_autonomo(text)

        detector_scores = [d1, d2, d3, d4, d5, d6, d7]
        score_final = _calc_final_score(detector_scores, pesos)
        evaluated.append(
            {
                "start": t,
                "end": t_end,
                "text": text,
                "score": score_final,
                "detectors": detector_scores,
            }
        )

        if score_final >= threshold:
            chosen_duration = _decide_duration(t, t_end, score_final, tipo)
            final_end = min(duration_total, t + chosen_duration)
            candidates.append(
                {
                    "start": t,
                    "end": final_end,
                    "text": text,
                    "score": round(score_final, 2),
                    "tipo": tipo,
                    "tiene_logica": bool(d4 > 0 and d7 >= 50),
                    "reason": (
                        f"D1:{d1:.0f} D2:{d2:.0f} D3:{d3:.0f} D4:{d4:.0f} "
                        f"D5:{d5:.0f} D6:{d6:.0f} D7:{d7:.0f}"
                    ),
                }
            )

        t += step

    # Controlled fallback: if strict threshold finds nothing, keep the best coherent windows.
    if not candidates:
        soft = []
        for item in evaluated:
            d1, d2, d3, d4, d5, d6, d7 = item["detectors"]
            if d4 == 0 or d3 < 10:
                continue
            if item["score"] < 48:
                continue
            chosen_duration = _decide_duration(item["start"], item["end"], item["score"], tipo)
            final_end = min(duration_total, item["start"] + chosen_duration)
            soft.append(
                {
                    "start": item["start"],
                    "end": final_end,
                    "text": item["text"],
                    "score": round(item["score"], 2),
                    "tipo": tipo,
                    "tiene_logica": bool(d4 > 0 and d7 >= 40),
                    "reason": (
                        f"D1:{d1:.0f} D2:{d2:.0f} D3:{d3:.0f} D4:{d4:.0f} "
                        f"D5:{d5:.0f} D6:{d6:.0f} D7:{d7:.0f}"
                    ),
                }
            )
        candidates = _remove_overlaps(soft, min_gap=12.0)

    final_candidates = _remove_overlaps(candidates, min_gap=12.0)

    if len(final_candidates) < max(1, int(num_clips)):
        micro = []
        for seg in ordered:
            text = (seg.get("text") or "").strip()
            if not text:
                continue
            start = float(seg.get("start", 0))
            end = max(float(seg.get("end", 0)), start + 1.0)

            d1 = _detector_emocion(text)
            d2 = 15.0
            d3 = _detector_semantico(text)
            d4 = _detector_narrativa(text, tipo)
            d5 = _detector_visual(start, end)
            d6 = _detector_ritmo([seg], start, end)
            d7 = _detector_contexto_autonomo(text)
            score = _calc_final_score([d1, d2, d3, d4, d5, d6, d7], pesos)

            if score < 32 or d4 == 0 or d3 < 10:
                continue

            natural = max(end - start, 1.0)
            dur = min(natural, 20.0)
            micro.append(
                {
                    "start": start,
                    "end": min(duration_total, start + dur),
                    "text": text,
                    "score": round(score, 2),
                    "tipo": tipo,
                    "tiene_logica": bool(d4 > 0 and d7 >= 40),
                    "reason": (
                        f"D1:{d1:.0f} D2:{d2:.0f} D3:{d3:.0f} D4:{d4:.0f} "
                        f"D5:{d5:.0f} D6:{d6:.0f} D7:{d7:.0f}"
                    ),
                }
            )

        if len(final_candidates) >= 1 and micro:
            # Preserve the strongest window candidate, then fill with non-overlapping micro moments.
            anchor = sorted(final_candidates, key=lambda x: x["score"], reverse=True)[:1]
            fill = _remove_overlaps(micro, min_gap=2.0)
            final_candidates = _remove_overlaps(anchor + fill, min_gap=2.0)
        elif micro:
            final_candidates = _remove_overlaps(micro, min_gap=2.0)

    final_candidates.sort(key=lambda x: x["score"], reverse=True)
    return final_candidates[: max(1, int(num_clips))]
