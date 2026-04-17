#!/usr/bin/env python3
"""
check_apis.py — Verifica que todas las APIs están configuradas y funcionan.
Ejecuta esto ANTES de arrancar los agentes por primera vez.

Uso: python scripts/check_apis.py
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

results = {}
all_ok = True

def check(name, test_fn, get_at, required=True):
    global all_ok
    print(f"  Verificando {name}...", end=" ", flush=True)
    try:
        ok, msg = test_fn()
        if ok:
            print(f"✅ {msg}")
            results[name] = "ok"
        else:
            print(f"❌ {msg}")
            print(f"     Consíguela en: {get_at}")
            results[name] = "missing"
            if required:
                all_ok = False
    except Exception as e:
        print(f"❌ Error: {e}")
        results[name] = "error"
        if required:
            all_ok = False

# ── TEST FUNCTIONS ────────────────────────────────────────────

def test_gemini():
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return False, "GEMINI_API_KEY no encontrada en .env"
    try:
        from google import genai
        client = genai.Client(api_key=key)
        r = client.models.generate_content(model="gemini-2.5-pro-preview-05-06", contents="di 'ok'")
        return True, f"Conectado ✓ (modelo: gemini-2.5-pro)"
    except Exception as e:
        return False, f"Error de conexión: {str(e)[:60]}"

def test_pexels():
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        return False, "PEXELS_API_KEY no encontrada — regístrate en pexels.com/api"
    import urllib.request
    req = urllib.request.Request(
        "https://api.pexels.com/v1/search?query=nature&per_page=1",
        headers={"Authorization": key}
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        if r.status == 200:
            return True, "Conectado ✓"
        return False, f"Status {r.status}"

def test_pixabay():
    key = os.getenv("PIXABAY_API_KEY")
    if not key:
        return False, "PIXABAY_API_KEY no encontrada — regístrate en pixabay.com/api/docs"
    import urllib.request
    url = f"https://pixabay.com/api/videos/?key={key}&q=nature&per_page=3"
    with urllib.request.urlopen(url, timeout=5) as r:
        if r.status == 200:
            return True, "Conectado ✓"
        return False, f"Status {r.status}"

def test_elevenlabs():
    key = os.getenv("ELEVENLABS_API_KEY")
    if not key:
        return False, "ELEVENLABS_API_KEY no encontrada — elevenlabs.io → Profile"
    import urllib.request, urllib.error
    req = urllib.request.Request(
        "https://api.elevenlabs.io/v1/user",
        headers={"xi-api-key": key}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            if r.status == 200:
                data = json.loads(r.read())
                chars = data.get("subscription", {}).get("character_count", "?")
                return True, f"Conectado ✓ ({chars} chars usados este mes)"
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return False, "API key inválida"
        return False, f"Error {e.code}"

def test_mongodb():
    url = os.getenv("MONGODB_URL")
    if not url:
        return False, "MONGODB_URL no encontrada — mongodb.com/atlas (free tier)"
    try:
        from pymongo import MongoClient
        client = MongoClient(url, serverSelectionTimeoutMS=5000)
        client.server_info()
        return True, "Conectado ✓"
    except Exception as e:
        return False, f"No se puede conectar: {str(e)[:60]}"

def test_youtube():
    cid = os.getenv("YOUTUBE_CLIENT_ID")
    csec = os.getenv("YOUTUBE_CLIENT_SECRET")
    if not cid or not csec:
        return False, "Falta YOUTUBE_CLIENT_ID o YOUTUBE_CLIENT_SECRET — console.cloud.google.com"
    if "your-client-id" in cid.lower() or len(cid) < 20:
        return False, "CLIENT_ID parece ser un placeholder — reemplázalo con el real"
    return True, "Keys presentes ✓ (OAuth se verifica en el primer upload)"

def test_google_tts():
    """Google TTS no necesita API key — usa gtts que es gratis"""
    try:
        from gtts import gTTS
        return True, "gtts disponible ✓ (fallback de ElevenLabs)"
    except ImportError:
        return False, "gtts no instalado — ejecuta: pip install gtts"

def test_ffmpeg():
    import subprocess
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        version = r.stdout.split("\n")[0].split("version ")[1].split(" ")[0] if "version" in r.stdout else "?"
        return True, f"ffmpeg {version} ✓"
    except FileNotFoundError:
        return False, "ffmpeg no instalado — brew install ffmpeg / apt install ffmpeg"

def test_whisper():
    try:
        import whisper
        return True, "whisper disponible ✓"
    except ImportError:
        return False, "whisper no instalado — pip install openai-whisper"

def test_pytrends():
    """Para Agent 09 Trend Hunter"""
    try:
        from pytrends.request import TrendReq
        return True, "pytrends disponible ✓"
    except ImportError:
        return False, "pytrends no instalado — pip install pytrends"

# ── EJECUTAR CHECKS ──────────────────────────────────────────

print("")
print("╔══════════════════════════════════════════════╗")
print("║  VidFlow AI — Verificación de APIs y Tools   ║")
print("╚══════════════════════════════════════════════╝")
print("")

print("📡 APIs Externas:")
check("Gemini 2.5 Pro",     test_gemini,     "aistudio.google.com",        required=True)
check("Pexels Video API",   test_pexels,     "pexels.com/api",             required=True)
check("Pixabay Video API",  test_pixabay,    "pixabay.com/api/docs",       required=True)
check("ElevenLabs TTS",     test_elevenlabs, "elevenlabs.io → Profile",    required=False)
check("MongoDB Atlas",      test_mongodb,    "mongodb.com/atlas",          required=True)
check("YouTube OAuth",      test_youtube,    "console.cloud.google.com",   required=True)

print("")
print("🛠️  Herramientas Locales:")
check("Google TTS (fallback)", test_google_tts, "pip install gtts",     required=False)
check("ffmpeg",                test_ffmpeg,     "brew/apt install ffmpeg", required=True)
check("Whisper (subtítulos)",  test_whisper,    "pip install openai-whisper", required=True)
check("pytrends (tendencias)", test_pytrends,   "pip install pytrends", required=False)

print("")
ok_count = sum(1 for v in results.values() if v == "ok")
total = len(results)
print(f"Resultado: {ok_count}/{total} servicios listos")

if all_ok:
    print("")
    print("✅ TODO LISTO — Puedes arrancar el sistema:")
    print("")
    print("  # Prueba un ciclo completo:")
    print("  bash scripts/run_agents.sh --once")
    print("")
    print("  # Arrancar modo continuo (mejora durante horas):")
    print("  nohup bash scripts/run_agents.sh --loop > logs/master.log 2>&1 &")
    print("  echo $! > logs/master.pid")
    print("")
    print("  # Monitor en tiempo real:")
    print("  bash scripts/watch_agents.sh")
else:
    print("")
    print("❌ Faltan APIs requeridas. Configúralas en .env y vuelve a ejecutar.")
    print("   Guía de configuración en: .github/copilot-instructions.md")
    sys.exit(1)
