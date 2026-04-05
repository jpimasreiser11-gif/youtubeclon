import json


VIRAL_SCRIPT_PROMPT = """
Eres un guionista experto en videos cortos virales para {plataforma} en el nicho {nicho}.
Idioma de salida obligatorio: {language}.
Genera un guion en 3 partes usando este input base:
- tema: {tema}
- hook: {hook}
- angulo: {angulo}
- palabras_clave: {palabras_clave}

Reglas obligatorias:
1) Debes devolver JSON VALIDO con llaves exactas: parte_1, parte_2, parte_3.
2) Cada parte debe tener entre 110 y 130 palabras.
3) Estructura por parte, en este orden:
    - Gancho: primeras 2 frases, empieza en medio del problema, usa hook del input.
    - Promesa: 1 frase con verbo de accion (descubre, evita, consigue, aplica).
    - Contenido: 3 puntos con formato afirmacion corta + explicacion + ejemplo numerico concreto.
    - Cierre: en parte_1 y parte_2 deja suspenso; en parte_3 CTA (seguir/suscribir/comentar/guardar).
4) Tono directo, cero relleno, sin introducciones largas.
5) No uses placeholders, no uses markdown, no agregues texto fuera del JSON.
"""


MYSTERY_SCRIPT_PROMPT = """
Eres un guionista experto en misterio, enigmas y conspiraciones para {plataforma}.
Idioma obligatorio: {language}.

Tema: {tema}
Hook base: {hook}
Angulo: {angulo}
Nicho: {nicho}
Palabras clave: {palabras_clave}

Reglas obligatorias:
1) Devuelve JSON valido con llaves exactas: parte_1, parte_2, parte_3.
2) Tono intimo: como contar un secreto en voz baja. Habla directo al espectador.
3) Frases cortas. Usa pausas dramaticas con "...".
4) El gancho debe aparecer en los primeros 3 segundos del texto de parte_1.
5) parte_1 y parte_2 terminan en cliffhanger. parte_3 cierra con pregunta para comentarios.
6) No escribas markdown ni explicaciones fuera del JSON.
"""


def _fallback_script(tema, hook, angulo):
    return {
        "parte_1": f"{hook} Hoy veras 3 errores sobre {tema}. Punto 1: lo que parece ahorro puede destruir tu flujo mensual.",
        "parte_2": f"Seguimos con {tema}. Punto 2: el sistema simple de 3 cuentas para ejecutar hoy y evitar deudas.",
        "parte_3": f"Cierre desde {angulo}. Punto 3: automatiza un habito semanal y mide en 30 dias. Sigue para mas tacticas.",
    }


def _fallback_script_en(tema, hook, angulo):
    return {
        "parte_1": f"{hook} Here is why most people fail with {tema}. First mistake: random actions without a clear system.",
        "parte_2": f"Now fix it fast. Use a 3-step framework for {tema}: simplify, execute, measure every week.",
        "parte_3": f"Final move from {angulo}: keep one KPI, iterate 30 days, and scale what works. Follow for more.",
    }


def _fallback_mystery_es(tema, hook):
    return {
        "parte_1": f"Escucha... {hook}. Nadie te lo cuenta asi. Todo empieza con {tema}, y una pista que no deberia existir.",
        "parte_2": "Los registros oficiales dicen una cosa... los testigos otra. Cada detalle encaja demasiado bien para ser casualidad.",
        "parte_3": "Y aqui viene lo inquietante... si esto fue real, alguien lo oculto. Tu que crees que paso realmente?",
    }


def _fallback_mystery_en(tema, hook):
    return {
        "parte_1": f"Listen... {hook}. Nobody tells it like this. It starts with {tema}, and one clue that should not exist.",
        "parte_2": "Official records say one thing... witnesses say another. Every detail fits too perfectly to be random.",
        "parte_3": "And here is the unsettling part... if this was real, someone buried the truth. What do you think happened?",
    }


def _is_mystery_mode(tema, nicho, hook):
    text = f"{tema} {nicho} {hook}".lower()
    return any(k in text for k in ["mister", "enigma", "conspir", "ocult", "secret", "mystery", "paranorm", "desaparec"])


def generate_script(tema, hook, angulo, nicho, plataforma="YouTube Shorts", palabras_clave=None, strict_rules=True, language="es"):
    mystery_mode = _is_mystery_mode(tema, nicho, hook)
    try:
        import ollama
        prompt = MYSTERY_SCRIPT_PROMPT if mystery_mode else VIRAL_SCRIPT_PROMPT
        response = ollama.chat(
            model="mistral",
            messages=[{
                "role": "user",
                "content": prompt.format(
                    tema=tema,
                    hook=hook,
                    angulo=angulo,
                    nicho=nicho,
                    plataforma=plataforma,
                    language=language,
                    palabras_clave=", ".join(palabras_clave or []),
                ),
            }],
            options={"temperature": 0.7 if strict_rules else 0.8, "num_predict": 1700},
        )
        raw = response["message"]["content"]
        start, end = raw.find("{"), raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
    except Exception:
        pass

    if mystery_mode and str(language).lower().startswith("en"):
        return _fallback_mystery_en(tema, hook)
    if mystery_mode:
        return _fallback_mystery_es(tema, hook)
    if str(language).lower().startswith("en"):
        return _fallback_script_en(tema, hook, angulo)
    return _fallback_script(tema, hook, angulo)
