import os
import json
import argparse
from datetime import datetime
import glob
import random

from viral_video_system.modules.module1_trends.trend_scraper import scrape_all
from viral_video_system.modules.module1_trends.trend_analyzer import analyze_trends
from viral_video_system.modules.module1_trends.monetizable_niche_finder import discover_top_monetizable_niches_en
from viral_video_system.modules.module2_motor_a.downloader import find_and_download_source
from viral_video_system.modules.module2_motor_a.peak_detector import detect_peak_moments
from viral_video_system.modules.module2_motor_a.transformer import add_transformative_value
from viral_video_system.modules.module3_motor_b.scriptwriter import generate_script
from viral_video_system.modules.module3_motor_b.video_factory import build_motor_b_video_suite, build_motor_b_dual_mystery_suite
from viral_video_system.shared.publisher import upload_to_youtube


def _build_mock_segments(analysis):
    hook1 = analysis.get("hook_numero_1", "Hay un patron oculto que casi nadie ve")
    hook2 = analysis.get("hook_numero_2", "Este error te esta frenando")
    angle = analysis.get("angulo_unico", "Metodo paso a paso")
    topic = analysis.get("tema_principal", "crecimiento")

    lines = [
        f"{hook1}. Te explico por que el {topic} falla en la mayoria.",
        "Nadie te cuenta esto: hay una pausa clave antes del resultado.",
        f"{hook2}. Si haces este ajuste hoy, cambia todo.",
        "Mira los numeros, en 30 dias la diferencia puede ser enorme.",
        f"{angle}. Paso uno: simplificar. Paso dos: medir. Paso tres: iterar.",
        "El problema real no es la estrategia, es la ejecucion diaria.",
        "Cuando aceleras demasiado al inicio, luego te quedas sin consistencia.",
        "Te dejo el ejemplo exacto para que lo copies y no pierdas tiempo.",
        "Esto parece obvio, pero casi nadie lo aplica de forma constante.",
        "Resultado final: menos ruido, mas enfoque y mejores decisiones.",
    ]

    segments = []
    t = 2.0
    for line in lines:
        dur = 10.0 + random.random() * 4.0
        segments.append({"start": round(t, 2), "end": round(t + dur, 2), "text": line})
        t += dur + random.uniform(0.6, 2.2)
    return segments


def _transcribe_source_segments(source_path):
    try:
        import whisper

        model_name = os.getenv("VIRAL_WHISPER_MODEL", "small")
        model = whisper.load_model(model_name)
        result = model.transcribe(source_path, language="es", word_timestamps=True, verbose=False)
        segments = result.get("segments") or []
        cleaned = []
        for seg in segments:
            cleaned.append(
                {
                    "start": float(seg.get("start", 0)),
                    "end": float(seg.get("end", 0)),
                    "text": (seg.get("text") or "").strip(),
                }
            )
        return cleaned
    except Exception:
        return []


def _load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _merge_analysis_with_seed(analysis, seed_input, niche):
    if not isinstance(seed_input, dict):
        return analysis

    merged = dict(analysis or {})
    tema = (seed_input.get("tema") or "").strip()
    hook = (seed_input.get("hook") or "").strip()
    angulo = (seed_input.get("angulo") or "").strip()
    seed_nicho = (seed_input.get("nicho") or niche or "").strip()
    palabras = seed_input.get("palabras_clave") or []
    palabras = [str(x).strip() for x in palabras if str(x).strip()]

    if tema:
        merged["tema_principal"] = tema
    if hook:
        merged["hook_numero_1"] = hook
    if angulo:
        merged["angulo_unico"] = angulo
    if seed_nicho:
        merged["niche"] = seed_nicho

    current_keywords = [str(x).strip() for x in (merged.get("palabras_clave") or []) if str(x).strip()]
    seen = set()
    final_keywords = []
    for kw in palabras + current_keywords:
        key = kw.lower()
        if key in seen:
            continue
        seen.add(key)
        final_keywords.append(kw)
    if final_keywords:
        merged["palabras_clave"] = final_keywords[:5]

    return merged


def _is_mystery_niche(text):
    low = (text or "").lower()
    return any(k in low for k in ["mister", "enigma", "conspir", "ocult", "secret", "mystery", "paranorm", "desaparec"])


def _normalize_script_parts(script_obj):
    if not isinstance(script_obj, dict):
        return None
    p1 = str(script_obj.get("parte_1") or "").strip()
    p2 = str(script_obj.get("parte_2") or "").strip()
    p3 = str(script_obj.get("parte_3") or "").strip()
    if not (p1 and p2 and p3):
        return None
    return {
        "parte_1": p1,
        "parte_2": p2,
        "parte_3": p3,
    }


def _extract_prebuilt_script(seed_input, language="es", mystery_mode=False):
    if not isinstance(seed_input, dict):
        return None

    prebuilt = seed_input.get("prebuilt_script")
    if not isinstance(prebuilt, dict):
        return None

    if "parte_1" in prebuilt:
        return _normalize_script_parts(prebuilt)

    es_script = _normalize_script_parts(prebuilt.get("es"))
    en_script = _normalize_script_parts(prebuilt.get("en"))

    if mystery_mode:
        if es_script or en_script:
            return {
                "es": es_script,
                "en": en_script,
            }
        return None

    lang_key = "en" if str(language).lower().startswith("en") else "es"
    chosen = en_script if lang_key == "en" else es_script
    return chosen or es_script or en_script


def run_pipeline(niche="finanzas personales", mode="auto", dry_run=True, youtube_credentials=None, seed_input=None, trend_mode="internet"):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    temp_dir = os.path.join(root, "viral_video_system", "temp")
    out_dir = os.path.join(root, "output_test", "viral_system")
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(out_dir, exist_ok=True)

    niche_scout = None
    effective_niche = niche

    if str(niche).strip().lower() in {"auto-monetizable-en", "auto-en", "best-en-niche"}:
        niche_scout = discover_top_monetizable_niches_en(limit=5)
        effective_niche = niche_scout.get("selected_niche", "personal finance")

    if trend_mode == "manual-only":
        trends = {
            "youtube": [],
            "twitter": [],
            "google": [],
            "generated_at": datetime.utcnow().isoformat() + "Z",
        }
        analysis = {
            "tema_principal": effective_niche,
            "hook_numero_1": "La mayoria falla por una razon que nadie explica.",
            "hook_numero_2": "Hay un patron oculto que puedes corregir hoy.",
            "angulo_unico": "Sistema paso a paso con numeros concretos",
            "palabras_clave": ["estrategia", "viral", "crecimiento", "dinero", "habitos"],
            "formato_recomendado": "motor_b",
            "razon_formato": "manual-only mode",
        }
    else:
        trends = scrape_all(effective_niche)
        analysis = analyze_trends(effective_niche, trends["youtube"], trends["twitter"], trends["google"])

    analysis = _merge_analysis_with_seed(analysis, seed_input, effective_niche)

    selected_mode = mode
    if mode == "auto":
        selected_mode = analysis.get("formato_recomendado", "motor_b")

    result = {
        "niche": effective_niche,
        "requested_niche": niche,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "dry_run": dry_run,
        "analysis": analysis,
        "trends": trends,
        "niche_scout": niche_scout or {},
        "trend_mode": trend_mode,
        "seed_input": seed_input or {},
        "selected_mode": selected_mode,
        "artifacts": {},
    }

    if selected_mode == "motor_a":
        source = find_and_download_source(analysis["tema_principal"], output_dir=temp_dir, dry_run=dry_run)
        segments = []
        source_path = source.get("filepath") or ""
        if source_path and os.path.exists(source_path) and not dry_run:
            segments = _transcribe_source_segments(source_path)
        if not segments:
            segments = _build_mock_segments(analysis)

        peaks = detect_peak_moments(
            segments,
            num_clips=6,
            title=source.get("title", analysis.get("tema_principal", "")),
            video_type="auto",
        )
        enriched = []
        for p in peaks:
            p["commentary"] = add_transformative_value(p["text"], analysis["tema_principal"], analysis["angulo_unico"])
            enriched.append(p)
        result["artifacts"]["source"] = source
        result["artifacts"]["peaks"] = enriched

    else:
        mystery_mode = _is_mystery_niche(analysis.get("tema_principal", "")) or _is_mystery_niche(analysis.get("niche") or niche)
        prebuilt = _extract_prebuilt_script(seed_input, mystery_mode=mystery_mode)

        if mystery_mode:
            prebuilt_es = prebuilt.get("es") if isinstance(prebuilt, dict) else None
            prebuilt_en = prebuilt.get("en") if isinstance(prebuilt, dict) else None

            script_es = prebuilt_es or generate_script(
                tema=analysis["tema_principal"],
                hook=analysis["hook_numero_1"],
                angulo=analysis["angulo_unico"],
                nicho=analysis.get("niche") or niche,
                palabras_clave=analysis.get("palabras_clave", []),
                strict_rules=True,
                language="es",
            )
            script_en = prebuilt_en or generate_script(
                tema=analysis["tema_principal"],
                hook=analysis["hook_numero_1"],
                angulo=analysis["angulo_unico"],
                nicho=analysis.get("niche") or niche,
                palabras_clave=analysis.get("palabras_clave", []),
                strict_rules=True,
                language="en",
            )
            suite = build_motor_b_dual_mystery_suite(
                script_by_lang={"es": script_es, "en": script_en},
                keywords=analysis.get("palabras_clave", []),
                out_dir=out_dir,
                temp_dir=temp_dir,
                dry_run=dry_run,
            )
            script = {"es": script_es, "en": script_en}
        else:
            script_language = "en" if (niche_scout and result["requested_niche"] in {"auto-monetizable-en", "auto-en", "best-en-niche"}) else "es"
            prebuilt_single = _extract_prebuilt_script(seed_input, language=script_language, mystery_mode=False)
            script = prebuilt_single or generate_script(
                tema=analysis["tema_principal"],
                hook=analysis["hook_numero_1"],
                angulo=analysis["angulo_unico"],
                nicho=analysis.get("niche") or niche,
                palabras_clave=analysis.get("palabras_clave", []),
                strict_rules=True,
                language=script_language,
            )
            suite = build_motor_b_video_suite(
                script=script,
                keywords=analysis.get("palabras_clave", []),
                out_dir=out_dir,
                temp_dir=temp_dir,
                dry_run=dry_run,
                language=script_language,
                style_profile="default",
            )

        final_built = suite.get("video_final_completo", "")
        try:
            publish_info = upload_to_youtube(
                video_path=final_built,
                title=analysis.get("hook_numero_1", "Clip viral"),
                description=analysis.get("angulo_unico", ""),
                tags=analysis.get("palabras_clave", []),
                dry_run=dry_run,
                credentials_data=youtube_credentials,
            )
        except Exception as publish_err:
            publish_info = {
                "platform": "youtube",
                "status": "failed",
                "error": str(publish_err),
            }

        result["artifacts"]["script"] = script
        result["artifacts"]["parts"] = suite.get("parts", [])
        result["artifacts"]["concat_list"] = suite.get("concat_list", "")
        result["artifacts"]["final_video"] = final_built
        if mystery_mode:
            result["artifacts"]["dual_channels"] = suite.get("channels", {})
            result["artifacts"]["mystery_mode"] = True
        result["artifacts"]["publish"] = publish_info

    out_json = os.path.join(out_dir, "last_run.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return out_json, result


def main():
    parser = argparse.ArgumentParser(description="Viral Video System pipeline")
    parser.add_argument("--niche", default="finanzas personales")
    parser.add_argument("--mode", default="auto", choices=["auto", "motor_a", "motor_b"])
    parser.add_argument("--dry-run", action="store_true", default=False)
    args = parser.parse_args()

    out_json, result = run_pipeline(niche=args.niche, mode=args.mode, dry_run=args.dry_run)
    print(f"Pipeline completed. Output JSON: {out_json}")
    print(f"Mode used: {result['selected_mode']}")


if __name__ == "__main__":
    main()
