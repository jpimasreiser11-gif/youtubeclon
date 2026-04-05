import json


ANALYSIS_PROMPT = """
Eres un estratega de contenido viral experto en {niche}.
Analiza estos datos de tendencias:

TITULOS YOUTUBE: {youtube_data}
TWEETS POPULARES: {twitter_data}
BUSQUEDAS EN ALZA: {google_data}

Devuelve UNICAMENTE JSON valido con:
{{
  "tema_principal": "string",
  "hook_numero_1": "string",
  "hook_numero_2": "string",
  "angulo_unico": "string",
  "palabras_clave": ["array", "de", "5", "keywords"],
  "formato_recomendado": "motor_a o motor_b",
  "razon_formato": "string corta"
}}
"""


def _fallback_analysis(niche, youtube_data, twitter_data, google_data):
    keywords = []
    for row in youtube_data[:5]:
        t = row.get("title", "")
        keywords.extend([w.lower() for w in t.split() if len(w) > 4][:2])
    if not keywords:
        keywords = ["ahorro", "deuda", "ingresos", "inversion", "habitos"]

    return {
        "tema_principal": niche,
        "hook_numero_1": "El error #1 que destruye tus finanzas sin que lo notes.",
        "hook_numero_2": "Lo que te dijeron sobre ahorrar esta incompleto.",
        "angulo_unico": "Micro-habitos diarios con evidencia practica",
        "palabras_clave": keywords[:5],
        "formato_recomendado": "motor_b" if len(google_data) >= 3 else "motor_a",
        "razon_formato": "Motor B evita riesgos de copyright cuando no hay fuente CC clara",
    }


def analyze_trends(niche, youtube_data, twitter_data, google_data):
    try:
        import ollama
        response = ollama.chat(
            model="mistral",
            messages=[{
                "role": "user",
                "content": ANALYSIS_PROMPT.format(
                    niche=niche,
                    youtube_data=str(youtube_data[:5]),
                    twitter_data=str(twitter_data[:10]),
                    google_data=str(google_data),
                )
            }],
        )
        raw = response["message"]["content"]
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception:
        pass

    return _fallback_analysis(niche, youtube_data, twitter_data, google_data)
