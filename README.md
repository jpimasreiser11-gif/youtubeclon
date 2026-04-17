# 🎬 Sistema Profesional Videos IA

**Automatización de producción de video para YouTube/TikTok con IA generativa.**

Sistema end-to-end profesional para operar 6+ canales de YouTube en paralelo con pipeline completamente automatizado:
- 📝 Generación de guiones con Gemini/local
- 🔊 Síntesis de voz con ElevenLabs/edge
- 📹 B-roll automático desde Pexels/Pixabay
- 🎞️ Montaje y encoding optimizado
- 🖼️ Thumbnails generados
- 📊 Metadata + SEO optimizado
- 📤 Publicación a YouTube
- 📈 Métricas y reportes

**6 canales configurados:**
- 🇪🇸 Impacto Mundial, Mentes Rotas, El Loco de la IA
- 🇬🇧 Mind Warp, Wealth Files, Dark Science

## 🚀 Inicio rápido

### 1. Instalación
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install

# Base de datos
python run.py setup-db
```

### 2. Configuración `.env`
```bash
cp .env.example .env
# Edita con tus API keys (ver Modo Gratis más abajo)
```

### 3. Ejecución local
```bash
# Terminal 1: API + Scheduler
python run.py server

# Terminal 2: Dashboard
cd frontend && npm run dev

# Terminal 3: Monitoreo (opcional)
tail -f logs/pipeline.log
```

### 4. Generar 1 video de prueba
```bash
python - <<'PY'
from backend.pipeline.orchestrator import run_single_channel
result = run_single_channel("impacto-mundial", upload=False)
import json
print(json.dumps(result, indent=2))
PY
```

## 💚 Modo Gratis (recomendado - completamente funcional)

Configura `.env` así para NO gastar dinero:

```env
SCRIPT_PROVIDER=local          # Usa templates locales, NO Gemini API
TTS_PRIMARY=edge               # Voz neural gratis de Microsoft Edge
GEMINI_API_KEY=                # Dejar vacío
ELEVENLABS_API_KEY=            # Dejar vacío
PEXELS_API_KEY=                # Dejar vacío (fallback a Wikimedia)
PIXABAY_API_KEY=               # Dejar vacío (fallback a Wikimedia)
YOUTUBE_DATA_API_KEY=          # Opcional: solo para tendencias
PIPELINE_RETRIES=2
```

**Resultado:** Videos de 5-15 minutos completamente gratis, sin cuota alguna.

## ⚙️ Parámetros operacionales (.env)

```env
# --- Límites por API (soft limits, solo warning)
QUOTA_YOUTUBE_DATA_API_DAILY=250
QUOTA_PEXELS_DAILY=500
QUOTA_PIXABAY_DAILY=500
QUOTA_ELEVENLABS_DAILY=400

# --- Ejecución del pipeline
PIPELINE_CHANNEL_DELAY_SECONDS=90      # Delay entre canales (evita saturación)
PIPELINE_AUTO_PAUSE_AFTER_ERRORS=3     # Auto-pausar canal después de 3 errores
PIPELINE_STRICT_MODE=false              # false=usar fallbacks, true=fallar en error

# --- Calidad de video
VIDEO_MIN_DURATION_SECONDS=240          # Mínimo 4 minutos
VIDEO_MAX_DURATION_SECONDS=1080         # Máximo 18 minutos
VIDEO_BITRATE_MBPS=8                    # Bitrate MP4 (calidad alta)

# --- Audio
ALLOW_SILENT_FALLBACK=false             # Fallar si audio es silencio
AUDIO_BITRATE_KBPS=192                  # AAC bitrate

# --- Agentes Pixel Agents
MAX_CONCURRENT_AGENTS=10                # Máximo agentes simultáneos
AGENT_SESSION_TIMEOUT_MINUTES=120       # Timeout por sesión (2h)

# --- Logging
LOG_LEVEL=INFO
ENABLE_DETAILED_PHASE_LOGS=true         # Log detallado por fase
```

## 📊 Ejecución y Métricas

### Local - Ejecutar 1 video
```bash
python - <<'PY'
from backend.pipeline.orchestrator import run_single_channel, save_pipeline_report
result = run_single_channel("impacto-mundial", upload=False)
print(f"Status: {result['status']}")
print(f"Time: {result['elapsed_seconds']}s")
for phase, time_s in result['phase_times'].items():
    print(f"  {phase}: {time_s}s")
PY
```

### Local - Ejecutar todos los canales
```bash
python - <<'PY'
from backend.pipeline.orchestrator import run_daily_pipeline, save_pipeline_report
from pathlib import Path
results = run_daily_pipeline(upload=False)
report_path = save_pipeline_report(results, Path("logs"))
print(f"Report: {report_path}")
PY
```

### Reportes generados
- `logs/pipeline_report_<TIMESTAMP>.json` — Métricas completas
- `logs/pipeline_summary_<TIMESTAMP>.txt` — Resumen humano-legible

## 🔄 Automatización con GitHub Actions

Workflows en `.github/workflows/`:

| Workflow | Cron | Qué hace |
|----------|------|----------|
| `daily_pipeline.yml` | `0 7 * * *` (7 AM UTC) | Genera 1 video por canal activo |
| `tiktok_clips.yml` | `0 9 * * *` (9 AM UTC) | Crea clips de 45s para TikTok |
| `weekly_report.yml` | `0 8 * * 1` (Lunes 8 AM) | Resumen semanal + webhook |
| `monetization_check.yml` | `0 0 * * 0` (Domingo) | Monitorea monetización |

### Setup de GitHub Actions

1. Fork este repositorio
2. Ve a `Settings → Secrets and variables → Actions`
3. Configura secrets (solo necesarios si NO usas Modo Gratis):
   ```
   GEMINI_API_KEY
   ELEVENLABS_API_KEY
   PEXELS_API_KEY
   PIXABAY_API_KEY
   REDDIT_CLIENT_ID
   REDDIT_CLIENT_SECRET
   YOUTUBE_DATA_API_KEY
   YOUTUBE_CLIENT_SECRETS_JSON (base64 de client_secret.json)
   YOUTUBE_TOKEN_JSON (base64 de token.json)
   ```

4. Habilita Actions y ejecuta `workflow_dispatch` en `daily_pipeline.yml`
5. Revisa los artifacts (videos en `daily-pipeline-<RUN_ID>`)

## 📦 CLI Directo (sin API)

```bash
# Generar script para un tema
python -m pipeline.generador_guion \
  --channel impacto-mundial \
  --topic "La ciencia detrás del sueño" \
  --script-provider local

# Descargar B-roll
python -m pipeline.downloader_footage \
  --channel impacto-mundial \
  --query "sleep science research" \
  --min-clips 15

# Montar video
python -m pipeline.ensamblador_pro \
  --channel impacto-mundial \
  --audio audio.wav \
  --script-file script.txt \
  --thumbnail thumb.jpg

# Control de calidad
python -m pipeline.quality_control \
  --video output.mp4 \
  --metadata-json metadata.json \
  --thumbnail thumb.jpg

# Subir a YouTube
python -m pipeline.youtube_uploader \
  --channel impacto-mundial \
  --video output.mp4 \
  --metadata-json metadata.json \
  --dry-run
```

## 🎬 Módulos Principales

- **`backend/pipeline/`** — Orquestador y fases (trend_finder, script_writer, voice_generator, video_builder, etc.)
- **`backend/database.py`** — SQLite con canales, videos, uso de API, trazas
- **`backend/config.py`** — Carga de `.env` + parámetros operacionales
- **`backend/runtime.py`** — QuotaManager + FallbackChain para gestión de recursos
- **`frontend/`** — Dashboard React (7 pestañas: Canales, Videos, Calendario, Analytics, Configuración, Logs, Agents)
- **`tests/run_phase7_checks.py`** — Smoke test completo

## 📈 Monitoreo y Alertas

### Webhooks (opcional)
```env
WEBHOOK_ERROR_ALERTS=https://discord.com/api/webhooks/YOUR_WEBHOOK
WEBHOOK_SUCCESS_REPORTS=https://discord.com/api/webhooks/YOUR_WEBHOOK
```

Los workflows de GitHub Actions pueden notificar directamente a Discord/Slack.

### Logging
```bash
# Ver logs en tiempo real
tail -f logs/pipeline.log

# Ver solo errores
grep ERROR logs/pipeline.log

# Generar reporte de sesión
python - <<'PY'
import json
from pathlib import Path
report = json.loads(Path("logs/pipeline_report_latest.json").read_text())
for ch in report['channels']:
    print(f"{ch['channel_id']}: {ch['status']} ({ch['elapsed_seconds']}s)")
PY
```

## 🔧 Troubleshooting

| Problema | Solución |
|----------|----------|
| "API quota exceeded" | Aumenta `QUOTA_*_DAILY` en `.env` o usa Modo Gratis |
| Video en blanco/silencio | Verifica que `BROLL_MIN_CLIPS`, `ALLOW_SILENT_FALLBACK` están OK |
| YouTube upload falla | Verifica `YOUTUBE_CLIENT_SECRETS_FILE` y `YOUTUBE_TOKEN_FILE` |
| Script muy corto | Aumenta `PIPELINE_MAX_TOPICS` o `SCRIPT_PROVIDER=gemini` (requiere API key) |
| Scheduler no ejecuta | Verifica que `python run.py server` está corriendo en Background |
| Base de datos locked | `rm data/youtube_automation.db` y vuelve a ejecutar `setup-db` |

## 📚 Documentación adicional

- [README_CONFIG.md](README_CONFIG.md) — Guía de configuración avanzada
- [ROADMAP.md](ROADMAP.md) — Plan de features futuras
- [FILE_REGISTRY.md](FILE_REGISTRY.md) — Índice de todos los módulos

## 📄 Licencia

MIT. Úsalo libremente. Mantén el crédito a Copilot.

---

**¿Preguntas?** Revisa `/tests/` para ejemplos de uso completo.

