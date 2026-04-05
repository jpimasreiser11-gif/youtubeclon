import time
import psycopg2
import os
from pathlib import Path
from dotenv import load_dotenv

# CRITICAL FIX: Load the correct .env file regardless of CWD
_REPO_ROOT = Path(__file__).parent.parent
_ENV_PATH = _REPO_ROOT / "app" / ".env"
if _ENV_PATH.exists():
    load_dotenv(dotenv_path=_ENV_PATH)
else:
    load_dotenv()


class JobProgressTracker:
    def __init__(self, project_id):
        self.project_id = project_id
        self.start_time = time.time()
        self.db_url = os.getenv("DATABASE_URL")

        # % range for each pipeline phase
        self.steps = {
            "downloading":  {"start": 0,  "end": 15},
            "audio_prep":   {"start": 15, "end": 20},
            "transcribing": {"start": 20, "end": 70},
            "analyzing":    {"start": 70, "end": 85},
            "refining":     {"start": 85, "end": 95},
            "rendering":    {"start": 95, "end": 100},
        }

        # ── Per-stage speed tracking ─────────────────────────────────────────
        # Key insight: each phase has a DIFFERENT speed.
        # Using overall elapsed/progress mix fast download with slow Whisper → bad ETA.
        # Instead: track speed WITHIN the current stage only.
        self._current_stage = None
        self._stage_start_time = None
        self._stage_start_percent = None

        # Smoothed ETA (exponential moving average — 70% previous, 30% new)
        self._last_eta = 0

    def update(self, step_key: str, current_percent: float, step_text: str = "Procesando..."):
        """
        step_key:        string identifier of the stage (to track speed changes)
        current_percent: 0-100 overall progress percent
        step_text:       human-readable message shown in the UI
        """
        current_percent = int(current_percent)

        # ── 1. Detect stage change → reset per-stage speed window ─────────────
        if self._current_stage != step_key:
            self._current_stage = step_key
            self._stage_start_time = time.time()
            self._stage_start_percent = current_percent
            # Keep _last_eta so the UI doesn't jump back to 0 between stages

        # ── 2. Compute ETA using only THIS stage's speed ──────────────────────
        stage_elapsed = time.time() - self._stage_start_time
        stage_progress_done = max(current_percent - self._stage_start_percent, 0)

        # Usar velocidades base por defecto basadas en la etapa para evitar que el ETA colapse a "0" o salte a horas
        # Si no hay progreso real todavía, usamos estas velocidades estimadas.
        base_speeds = {
            "downloading": 0.8,  # Rápido: ~1% cada 1.2s
            "transcribing": 0.08, # Lento: Whisper toma su tiempo
            "analyzing": 0.5,    # Rápido: LLM
            "refining": 0.3,     # Medio: Crop y cálculo
            "rendering": 0.15    # Medio-lento: FFmpeg
        }
        
        expected_speed = base_speeds.get(step_key, 0.2)
        
        # Mezclamos la velocidad esperada con la velocidad real observada gradualmente
        if stage_progress_done > 0 and stage_elapsed >= 5:
            real_speed = stage_progress_done / stage_elapsed
            # Si la etapa se atasca (ej: al 59%), la velocidad real cae a 0.
            # Nunca dejamos que la velocidad baje más que la mitad de la esperada para evitar ETAs infinitos
            speed_pct_per_sec = max(real_speed, expected_speed * 0.3)
        else:
            speed_pct_per_sec = expected_speed

        remaining_total = 100 - current_percent
        raw_eta = int(remaining_total / speed_pct_per_sec)

        # Suavizado ETA 50/50 para que no salte drásticamente
        if self._last_eta > 0:
            eta_seconds = int((raw_eta + self._last_eta) / 2)
        else:
            eta_seconds = raw_eta
            
        self._last_eta = eta_seconds

        # ── 3. Write to DB ─────────────────────────────────────────────────────
        try:
            conn = psycopg2.connect(self.db_url)
            cur = conn.cursor()
            cur.execute("""
                UPDATE projects
                SET progress_percent = %s,
                    eta_seconds      = %s,
                    current_step     = %s
                WHERE id = %s::uuid
            """, (current_percent, eta_seconds, step_text, self.project_id))
            conn.commit()
            cur.close()
            conn.close()

            eta_fmt = f"{eta_seconds // 60}m {eta_seconds % 60}s" if eta_seconds > 0 else "calculando..."
            print(f"📊 Progreso: {current_percent}% | ETA: {eta_fmt} | {step_text}")
        except Exception as e:
            print(f"⚠️ Error actualizando progreso: {e}")
