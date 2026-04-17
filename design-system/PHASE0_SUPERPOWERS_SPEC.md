# Fase 0 - Superpowers Brainstorming + Spec

## 1) Brainstorming (resultado)

### MVP Dia 1 (debe funcionar en los 6 canales)
1. Pipeline end-to-end por canal: `trend_finder -> script_writer -> voice_generator -> video_builder -> thumbnail_creator -> metadata_writer`.
2. Ejecucion manual de un canal desde UI y CLI (`/generator` + `run.py generate`).
3. Persistencia completa en SQLite (`channels`, `videos`, `trends`, `pipeline_logs`).
4. Estado visible en Dashboard (estado, errores, actividad reciente).
5. Fallback activo cuando fallen trends/APIs (seed topics por canal + retries).

### Modulo de mayor riesgo tecnico
`video_builder` por dependencia de sincronizacion audio/B-roll/render, tiempos de IO, codecs y calidad final.

### Estructura para escalar a canal 7+
- Configuracion data-driven por `channels` table y no por condicionales.
- Directorios por canal derivados de `channel_id` (ya existe en `backend/config.py`).
- Pipeline stateless por paso + logging fuerte en `pipeline_logs`.
- UI basada en datos (`fetchChannels`) sin hardcode de layout por canal.

### Si falla una API gratuita (arbol de fallback)
1. Trend API falla -> usar `seed_topics`.
2. LLM falla en script -> retry con backoff -> template minimo por nicho.
3. TTS premium falla -> fallback local (`edge-tts`/`gTTS`).
4. B-roll falla -> usar clips locales o pantalla de soporte.
5. Upload falla -> marcar `ready` para reintento manual/scheduler.

### Como medir "calidad humana"
- Hook quality score (0-100) y retencion estimada por estructura.
- Densidad de frases repetidas + deteccion de muletillas IA.
- WPM real en audio vs objetivo por canal.
- QA visual: thumbnail legible + subtitulos sincronizados.
- KPI post-publicacion: CTR, retencion 30s, comentarios cualitativos.

---

## 2) Arquitectura tecnica (actual + objetivo inmediato)

### Frontend
- React + Vite, 7 tabs: Dashboard, Channels, Ideas, Generator, Library, Scheduler, Settings.
- API client central en `frontend/src/api.js`.

### Backend
- FastAPI (`backend/server.py`) con rutas: channels, videos, pipeline, analytics, ideas, scheduler.
- Scheduler APScheduler para publicaciones.

### Pipeline
- Orquestador central: `backend/pipeline/orchestrator.py`.
- Modulos: `trend_finder.py`, `script_writer.py`, `voice_generator.py`, `video_builder.py`, `thumbnail_creator.py`, `metadata_writer.py`, `publisher.py`.

### Estado compartido
- SQLite en `data/youtube_automation.db`.
- Tabla de trazas operativas: `pipeline_logs`.

---

## 3) Contratos de interfaz entre modulos (v1)

```python
# trend_finder -> script_writer
TrendResult = {
    "topic": str,
    "score": float,
    "source": str,
    "context_json": dict,
}

# script_writer -> voice_generator + video_builder
ScriptResult = {
    "title": str,
    "script": str,
    "broll_markers": list[dict],  # [{"query": str, "start": int, "end": int}]
    "hook": str,
    "cta": str,
}

# voice_generator -> video_builder
AudioResult = {
    "audio_path": str,
    "duration_seconds": float,
    "srt_path": str,
    "wpm": float,
}

# video_builder -> publisher
VideoBuildResult = {
    "video_path": str,
    "duration_seconds": float,
    "thumbnail_path": str,
}
```

---

## 4) Criterios de aceptacion por modulo

1. `trend_finder`: retorna >=1 topic util o fallback seed topic.
2. `script_writer`: produce guion completo + titulo + markers.
3. `voice_generator`: audio valido y duracion > 0.
4. `video_builder`: archivo de video reproducible.
5. `thumbnail_creator`: thumbnail generado y legible.
6. `metadata_writer`: title/description/tags completos.
7. `publisher`: URL o estado `ready` con error explicito.
8. `orchestrator`: pipeline completo con `status` final y logs.

---

## 5) Plan ordenado con dependencias

1. Endurecer contratos de datos entre modulos (tipos/campos obligatorios).
2. Blindar `video_builder` con validaciones previas de entradas.
3. Normalizar logs de errores para reintentos inteligentes.
4. Agregar chequeo de "human quality" antes de publicar.
5. Integrar Scheduler + Publisher con reintento seguro.

Dependencias clave:
- (1) antes de (2), (4) y (5).
- (3) en paralelo con (2).
- (4) antes de publicar automatico en (5).

---

## 6) Tests de aceptacion (definidos para Fase siguiente)

1. Trigger manual genera un video `ready` sin excepciones.
2. Si falla trends API, pipeline usa seed topic y continua.
3. Si falla TTS principal, se usa fallback y hay log de degradacion.
4. Video final existe en disco y metadata_json se persiste.
5. Scheduler crea/cancela jobs y respeta estados.
6. Dashboard refleja actividad reciente luego de ejecucion.

