import os
import argparse
import time
import json
import subprocess
import shutil
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
import psycopg2  # CRITICAL FIX: Ensure DB connection works directly
import re
from collections import Counter

# Add project root to path
ROOT_DIR = str(Path(__file__).parent.parent.parent)
sys.path.append(ROOT_DIR)
# FIX: sovereign_core está en app/scripts, no en scripts raíz
sys.path.append(os.path.join(ROOT_DIR, 'app', 'scripts'))
sys.path.append(os.path.join(ROOT_DIR, 'scripts'))
from progress_tracker import JobProgressTracker

# FORCE UTF-8 ENCODING (Windows Fix)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# DEBUG: Single log file (overwritten each run, no file spam)
debug_log_path = None
try:
    debug_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_ingest.log")
    with open(debug_log_path, "w", encoding="utf-8") as f:
        f.write(f"Started at {time.ctime()}\n")
        f.write(f"CWD: {os.getcwd()}\n")
        f.write(f"Executable: {sys.executable}\n")
except Exception as e:
    debug_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_ingest_fallback.log")

# CRITICAL FIX: Rutas relativas dinámicas (Adiós al C:\Users\jpima...)
FFMPEG_EXE = os.path.join(ROOT_DIR, "data", "ffmpeg.exe")
if not os.path.exists(FFMPEG_EXE):
    FFMPEG_EXE = "ffmpeg" # Fallback al sistema si está instalado globalmente

ffmpeg_dir = os.path.dirname(FFMPEG_EXE)
if ffmpeg_dir and ffmpeg_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] += os.pathsep + ffmpeg_dir
    try:
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"Added FFmpeg to PATH: {ffmpeg_dir}\n")
    except: 
        pass

# Configuracion Base Dinámica
STORAGE_BASE = os.path.join(ROOT_DIR, "app", "storage")
os.makedirs(STORAGE_BASE, exist_ok=True)
os.makedirs(os.path.join(STORAGE_BASE, "temp"), exist_ok=True)
os.makedirs(os.path.join(STORAGE_BASE, "clips"), exist_ok=True)
os.makedirs(os.path.join(STORAGE_BASE, "processed"), exist_ok=True)
os.makedirs(os.path.join(STORAGE_BASE, "thumbnails"), exist_ok=True)

# Import ViralEngine con fallback robusto
ViralEngine = None
try:
    from sovereign_core import ViralEngine
    with open(debug_log_path, "a", encoding="utf-8") as f:
        f.write("✅ Import ViralEngine SUCCESS (direct)\n")
except ImportError:
    try:
        from app.scripts.sovereign_core import ViralEngine
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write("✅ Import ViralEngine SUCCESS (app.scripts path)\n")
    except Exception as e:
        import traceback
        with open(debug_log_path, "a", encoding="utf-8") as f:
            f.write(f"❌ Import ViralEngine FAILED: {e}\n")
            f.write(traceback.format_exc())
        sys.exit(1)

# Robust .env loading
env_path = os.path.join(ROOT_DIR, 'app', '.env')
if not os.path.exists(env_path):
    # Try ROOT_DIR just in case
    env_path = os.path.join(ROOT_DIR, '.env')

load_dotenv(env_path)

DB_CONFIG = {
    "user": os.getenv("POSTGRES_USER", "n8n"),
    "password": os.getenv("POSTGRES_PASSWORD", "n8n"),
    "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
    "port": os.getenv("POSTGRES_PORT", "5432"),
    "database": os.getenv("POSTGRES_DB", "antigravity")
}

# Debug DB Config
logger = logging.getLogger("IngestWrapper")
# Print masked password for debugging
debug_config = DB_CONFIG.copy()
debug_config['password'] = '******'
print(f"DEBUG: Using DB Config: {debug_config}")

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("IngestWrapper")

def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"⚠️ DB Connection Failed: {e}")
        return None

def update_project_status(project_id, status, progress=None, estimated_time=None):
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        # Mapeo de seguridad para evitar crashes en Postgres
        valid_statuses = ['QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED']
        safe_status = status if status in valid_statuses else 'FAILED'
        
        # Como usamos JobProgressTracker, solo actualizamos el estado maestro aquí
        cur.execute("UPDATE projects SET project_status = %s::job_status WHERE id = %s::uuid", (safe_status, project_id))
        conn.commit()
    except Exception as e:
        logger.error(f"Error updating status: {e}")
    finally:
        cur.close()
        conn.close()


# ------------------ Viral scoring & metadata helpers ------------------
STOPWORDS = set([
    # English (small set)
    'the','that','have','this','with','from','they','will','would','there','their','about','which','when','what','where','who','how','why','your','you','for','and','but','not','are','was','were','been','is','a','an','in','on','at','of','to',
    # Spanish (small set)
    'que','por','para','con','sin','sobre','entre','como','pero','como','más','menos','esta','esta','este','esta','este','estos','estas','usted','tu','tú','las','los','un','una','unos','unas'
])

def words_to_text(words):
    try:
        if not words:
            return ''
        if isinstance(words, str):
            return words
        parts = []
        for w in words:
            if isinstance(w, str):
                parts.append(w)
            elif isinstance(w, dict):
                t = w.get('text') or w.get('word') or w.get('token') or w.get('value')
                if t:
                    parts.append(str(t))
            else:
                parts.append(str(w))
        return ' '.join(parts)
    except Exception:
        return ''

def extract_keywords(text, n=5):
    if not text:
        return []
    text_low = text.lower()
    text_clean = re.sub(r'[^a-z0-9áéíóúüñ\s]', ' ', text_low)
    tokens = [t for t in text_clean.split() if len(t) > 3 and t not in STOPWORDS]
    if not tokens:
        return []
    counts = Counter(tokens)
    return [w for w,_ in counts.most_common(n)]

def detect_hook(text):
    if not text:
        return ''
    parts = re.split(r'[\.\!\?\n]+', text.strip())
    if not parts:
        return ''
    first = parts[0].strip()
    if not first:
        return ''
    qwords = ['what','how','why','when','where','who','do','did','¿','por','cómo','qué','por qué','quién']
    for q in qwords:
        if q in first.lower():
            return first
    # fallback: return a short excerpt
    words = first.split()
    return ' '.join(words[:12])

def generate_title(text, meta=None, max_len=60):
    if meta and meta.get('title'):
        return meta.get('title')[:max_len]
    hook = detect_hook(text)
    if hook:
        return hook[:max_len]
    kws = extract_keywords(text, n=3)
    if kws:
        return ' '.join(kws).title()[:max_len]
    words = text.split()
    return ' '.join(words[:8])[:max_len]

def score_and_enrich_results(results):
    enriched = []
    for res in results:
        meta = (res.get('metadata') or {})
        words_list = res.get('words', [])
        transcript = words_to_text(words_list)
        base = int(meta.get('virality_score', 50)) if meta.get('virality_score') is not None else 50
        duration = float(res.get('duration') or 0)
        score = base
        # Duration heuristic: sweet spot 8-25s
        if 8 <= duration <= 25:
            score += 12
        elif 25 < duration <= 45:
            score += 5
        elif duration < 6:
            score -= 15
        elif duration > 60:
            score -= int((duration - 60) / 2)

        # Hook presence
        hook = meta.get('hook') or detect_hook(transcript)
        if hook:
            score += 15
            meta['hook'] = hook

        # Keywords / hashtags
        keywords = extract_keywords(transcript, n=5)
        if keywords:
            score += min(10, len(keywords) * 2)
            meta['hashtags'] = ' '.join('#' + k for k in keywords[:5])
        else:
            meta['hashtags'] = ''

        # Uniqueness bonus
        tokens = re.findall(r'\w+', transcript.lower())
        unique_ratio = len(set(tokens)) / max(1, len(tokens))
        score += int(unique_ratio * 5)

        # Final clamp
        score = max(0, min(100, int(score)))
        meta['composite_score'] = score

        # Title fallback
        meta['title'] = meta.get('title') or generate_title(transcript, meta)

        res['metadata'] = meta
        enriched.append(res)

    enriched.sort(key=lambda r: r.get('metadata', {}).get('composite_score', 0), reverse=True)
    return enriched


def _probe_duration_seconds(video_path):
    try:
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path,
        ]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8', errors='ignore').strip()
        return max(1.0, float(out))
    except Exception:
        return 0.0


def _find_best_source_video(temp_dir):
    candidates = []
    for root, _, files in os.walk(temp_dir):
        for name in files:
            low = name.lower()
            if not low.endswith('.mp4'):
                continue
            if low.endswith('_subtitled.mp4'):
                continue
            path = os.path.join(root, name)
            try:
                size = os.path.getsize(path)
            except Exception:
                size = 0
            candidates.append((size, path))

    if not candidates:
        return ''

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


def _build_fallback_clip(temp_dir):
    source = _find_best_source_video(temp_dir)
    if not source:
        return None

    source_duration = _probe_duration_seconds(source)
    if source_duration <= 1.0:
        return None

    clip_duration = min(45.0, max(15.0, source_duration * 0.35))
    out_path = os.path.join(temp_dir, 'fallback_clip.mp4')

    cmd = [
        FFMPEG_EXE,
        '-y',
        '-i', source,
        '-ss', '0',
        '-t', str(round(clip_duration, 2)),
        '-vf', 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        out_path,
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        logger.warning(f'Fallback clip render failed: {e}')
        return None

    if not os.path.exists(out_path):
        return None

    return {
        'path': out_path,
        'duration': clip_duration,
        'words': [],
        'metadata': {
            'virality_score': 60,
            'title': 'Fallback clip generado automaticamente',
            'description': 'No se detectaron segmentos fuertes; se genero un clip base para no romper el flujo.',
            'hook': 'Clip fallback: revisar manualmente para mejorar resultado',
            'payoff': 'Puedes volver a intentar con otro video o activar opciones enterprise.',
            'hashtags': '#clip #viral #shorts',
        },
    }

# ------------------ End helpers ------------------


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_id", help="UUID of the project")
    parser.add_argument("url", help="Video source URL")
    # Flags opcionales (ignorados por ahora en esta version simplificada del wrapper, pero mantenidos para compatibilidad)
    parser.add_argument("--audio-pro", action="store_true")
    parser.add_argument("--smart-reframe", action="store_true")
    parser.add_argument("--clean-speech", action="store_true")
    parser.add_argument("--b-roll", action="store_true")
    
    args = parser.parse_args()
    
    project_id = args.project_id
    url = args.url
    
    print(f"Iniciando Sovereign Engine para Proyecto {project_id}")
    logger.info(f"Start processing project {project_id} with URL {url}")
    
    results = []
    clips_generated_count = 0
    clips_saved_successfully = False  # Inicializar ANTES del try
    
    try:
        start_time = time.time()
        
        # 1. Definir callback de progreso para la UI (Weight-based ETA Engine)
        tracker = JobProgressTracker(project_id)

        # BUG 5 FIX: Send an immediate progress update so the UI shows > 0% right away
        tracker.update("downloading", 0.0, "Iniciando descarga del video...")
        def on_progress(stage, percent):
            # Mapear estados de ingest a los del tracker
            lower_stage = stage.lower()
            step_key = "analyzing" # default fallback
            
            if "descargando" in lower_stage:
                step_key = "downloading"
            elif "transcribiendo" in lower_stage:
                step_key = "transcribing"
            elif "renderizando" in lower_stage:
                step_key = "rendering"
            elif "audio" in lower_stage:
                step_key = "audio_prep"
            elif "clip" in lower_stage or "procesando" in lower_stage:
                step_key = "refining"
                
            tracker.update(step_key, percent, stage)
            
        # 2. Inicializar Motor - NUEVO: Auto-detectar provider disponible y pasar opciones
        groq_api_key = os.getenv("GROQ_API_KEY")
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        
        if groq_api_key:
            api_key = groq_api_key
            provider = "groq"
        elif gemini_api_key:
            api_key = gemini_api_key
            provider = "gemini"
        else:
            raise ValueError("No API key encontrada")
            
        # Opciones Enterprise recopiladas de los argumentos de CLI
        enterprise_options = {
            "audio_pro": args.audio_pro,
            "smart_reframe": args.smart_reframe,
            "clean_speech": args.clean_speech,
            "b_roll": args.b_roll
        }

        # Usar carpeta temporal para procesamiento
        temp_dir = os.path.join(STORAGE_BASE, "temp", project_id)
        
        # 🚨 FORZAR GEMINI 🚨: Groq da errores 403 Forbidden y cuelga el proceso al 69%
        engine = ViralEngine(
            api_key, 
            output_dir=temp_dir, 
            ffmpeg_path=FFMPEG_EXE, 
            provider=provider,
            options=enterprise_options
        )
        
        # 3. Ejecutar Pipeline
        results = engine.run_pipeline(url, on_progress=on_progress)

        # 3.1 Enrich & score results, then select top clips
        try:
            enriched_results = score_and_enrich_results(results)
        except Exception as e:
            logger.warning(f"Scoring/enrichment failed: {e}")
            enriched_results = results or []
        
        # 4. Guardar Clips en DB y Mover Archivos
        conn = get_db_connection()
        if not conn:
            raise Exception("No hay conexión a DB para guardar clips")
            
        cur = conn.cursor()

        # Compatibility layer: some deployments still use the old clips schema
        # without title/description/hook/payoff columns.
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'clips'
            """
        )
        clip_columns = {row[0] for row in cur.fetchall()}
        has_extended_clip_cols = all(
            c in clip_columns
            for c in ("title_generated", "description_generated", "hook_description", "payoff_description")
        )
        
        if not enriched_results or len(enriched_results) == 0:
            logger.warning("No se generaron clips válidos. Intentando fallback automatico...")
            fallback = _build_fallback_clip(temp_dir)
            if fallback:
                enriched_results = [fallback]
                logger.info("Fallback clip generado correctamente.")
            else:
                logger.warning("Fallback no disponible. Marcando proyecto como FAILED.")
                cur.execute(
                    "UPDATE projects SET project_status = 'FAILED', current_step = 'Sin clips viables', progress_percent = 100, error_log = 'El video no contenía segmentos que superaran los requisitos mínimos de viralidad y duración. Prueba con otro video más largo.' WHERE id = %s;",
                    (project_id,)
                )
                conn.commit()
                cur.close()
                conn.close()
                return
        
        # Limit number of clips saved to a reasonable amount (e.g., top 6)
        max_clips = min(6, len(enriched_results))
        clips_generated_count = max_clips
        print(f"Saving top {max_clips} of {len(enriched_results)} clips to DB and scheduling uploads...")

        for i, res in enumerate(enriched_results[:max_clips]):
            meta = res['metadata']
            temp_path = res['path']
            
            # Insertar clip
            if has_extended_clip_cols:
                cur.execute("""
                    INSERT INTO clips (
                        project_id, start_time, end_time, virality_score, transcript_json,
                        title_generated, description_generated, hook_description, payoff_description
                    )
                    VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    project_id,
                    0.0,
                    res['duration'],
                    int(meta.get('composite_score', meta.get('virality_score', 85))),
                    json.dumps(res.get('words', [])),
                    meta.get('title', 'Viral Clip'),
                    f"{meta.get('description', '')}\n\n{meta.get('hashtags', '')}",
                    meta.get('hook', ''),
                    meta.get('payoff', '')
                ))
            else:
                cur.execute("""
                    INSERT INTO clips (
                        project_id, start_time, end_time, virality_score, transcript_json
                    )
                    VALUES (%s::uuid, %s, %s, %s, %s)
                    RETURNING id;
                """, (
                    project_id,
                    0.0,
                    res['duration'],
                    int(meta.get('composite_score', meta.get('virality_score', 85))),
                    json.dumps(res.get('words', [])),
                ))
            
            clip_id = cur.fetchone()[0]
            
            # Mover archivo a storage/clips/{uuid}.mp4
            final_path = os.path.join(STORAGE_BASE, "clips", f"{clip_id}.mp4")
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            
            if os.path.exists(temp_path):
                shutil.move(temp_path, final_path)
            
            # Copiar también a storage/processed/ (necesario para proxy-video API)
            processed_path = os.path.join(STORAGE_BASE, "processed", f"{clip_id}.mp4")
            os.makedirs(os.path.dirname(processed_path), exist_ok=True)
            if os.path.exists(final_path):
                shutil.copy2(final_path, processed_path)
            
            # Crear entrada en video_versions (necesario para que la UI encuentre el archivo)
            cur.execute("INSERT INTO video_versions (clip_id, version, file_path) VALUES (%s, 'preview', %s)", (clip_id, final_path))
            
            # Thumbnail (Usamos el mismo video como source para ffmpeg thumbnail)
            thumb_path = os.path.join(STORAGE_BASE, "thumbnails", f"{clip_id}.jpg")
            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
            
            # Generar thumb
            subprocess.run([
                FFMPEG_EXE, "-y",
                "-i", final_path, "-ss", "00:00:01", "-vframes", "1", thumb_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            cur.execute("INSERT INTO thumbnails (clip_id, url) VALUES (%s, %s)", (clip_id, thumb_path))
            
            # --- AUTO UPLOAD TO TIKTOK & YOUTUBE ---
            safe_title_for_cli = "".join(c for c in meta.get('title', 'Viral Clip') if c.isalnum() or c in (' ', '-', '_'))[:40]
            desc = f"{meta.get('hook', 'Amazing video!')} #shorts #viral #fyp"
            
            # Calculate delay: 0 hours for the first clip, 3 hours for the second, 6 for the third...
            delay_hours = i * 3
            
            # NUEVO: Usar Playwright para TikTok (más estable)
            tiktok_script = os.path.join(os.path.dirname(__file__), "upload_tiktok_playwright.py")
            yt_script = os.path.join(os.path.dirname(__file__), "upload_youtube_selenium.py")
            
            logger.info(f"Programando Auto-Upload en {delay_hours}h para: {safe_title_for_cli}")
            try:
                # Prepare child env with UTF-8 IO to avoid encoding errors
                child_env = os.environ.copy()
                child_env['PYTHONIOENCODING'] = 'utf-8'

                # Ensure upload logs folder exists
                upload_logs_dir = os.path.join(STORAGE_BASE, "upload_logs")
                os.makedirs(upload_logs_dir, exist_ok=True)

                tiktok_log = os.path.join(upload_logs_dir, f"{clip_id}_tiktok.log")
                yt_log = os.path.join(upload_logs_dir, f"{clip_id}_youtube.log")

                # Open log files and spawn processes directing stdout/stderr there
                tiktok_f = open(tiktok_log, 'a', encoding='utf-8')
                yt_f = open(yt_log, 'a', encoding='utf-8')
                tiktok_f.write(f"=== START {time.ctime()} ===\n")
                yt_f.write(f"=== START {time.ctime()} ===\n")

                tiktok_proc = subprocess.Popen([
                    sys.executable, tiktok_script,
                    "--video", final_path,
                    "--caption", desc,
                    "--delay_hours", str(delay_hours)
                ], stdout=tiktok_f, stderr=subprocess.STDOUT, env=child_env)

                yt_proc = subprocess.Popen([
                    sys.executable, yt_script,
                    "--video", final_path,
                    "--title", safe_title_for_cli,
                    "--description", desc,
                    "--privacy", "public",
                    "--delay_hours", str(delay_hours)
                ], stdout=yt_f, stderr=subprocess.STDOUT, env=child_env)

                # Close parent file handles (child keeps writing)
                tiktok_f.close()
                yt_f.close()

            except Exception as e:
                logger.error(f"Error launching auto-uploads: {e}")
                try:
                    cur.execute("UPDATE projects SET error_log = COALESCE(error_log, '') || %s WHERE id = %s", (f"Upload spawn error: {e}\n", project_id))
                    conn.commit()
                except Exception as e2:
                    logger.error(f"Failed to write spawn error to DB: {e2}")
            # ---------------------------------------
            
        conn.commit()
        cur.close()
        conn.close()
        
        clips_saved_successfully = True
        
    except Exception as e:
        logger.error(f"Error guardando clips en DB: {e}")
        import traceback
        traceback.print_exc()
        clips_saved_successfully = False
    
    # CRITICAL FIX: Actualizar status FUERA del try principal
    try:
        if clips_saved_successfully:
            final_count = clips_generated_count if clips_generated_count > 0 else len(results)
            tracker.update("rendering", 1.0, f"Completado: {final_count} clips generados")
            update_project_status(project_id, 'COMPLETED', 100)
            conn_ok = get_db_connection()
            if conn_ok:
                try:
                    cur_ok = conn_ok.cursor()
                    cur_ok.execute(
                        "UPDATE projects SET error_log = '', current_step = %s WHERE id = %s::uuid",
                        (f"Completado: {final_count} clips generados", project_id),
                    )
                    conn_ok.commit()
                    cur_ok.close()
                finally:
                    conn_ok.close()
            logger.info(f"Proyecto {project_id} completado: {final_count} clips generados")
            sys.exit(0)
        else:
            tracker.update("rendering", 0.0, "Error generando clips")
            update_project_status(project_id, 'FAILED')
            logger.error(f"Proyecto {project_id} falló")
            sys.exit(1)
    except Exception as status_err:
        logger.error(f"Error actualizando status final: {status_err}")
        sys.exit(1)
    
    # Limpieza (mejor esfuerzo, no crítico)
    try:
        shutil.rmtree(temp_dir)
        logger.info(f"Limpieza completada: {temp_dir} eliminado")
    except Exception as cleanup_err:
        logger.warning(f"No se pudo limpiar temp_dir: {cleanup_err}")

if __name__ == "__main__":
    main()
