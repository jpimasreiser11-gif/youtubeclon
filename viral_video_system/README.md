# Viral Video System (Parallel Migration)

Este paquete implementa la nueva arquitectura que compartiste, pero en paralelo al sistema actual para no romper nada.

## Objetivo
- Mantener flujo actual operativo (`app/scripts/ingest.py`, worker, web).
- Activar nueva arquitectura progresivamente.
- Soportar modo `dry-run` sin dependencias pesadas.

## Estructura
- `viral_video_system/config/`: nichos, canales CC, perfiles de voz
- `viral_video_system/modules/module1_trends/`: scraping + análisis
- `viral_video_system/modules/module2_motor_a/`: reciclaje transformativo
- `viral_video_system/modules/module3_motor_b/`: generación IA
- `viral_video_system/shared/`: subtítulos, ensamblado, publicación
- `scripts/run_viral_pipeline.py`: puente compatible

## Uso rápido
```powershell
python scripts/run_viral_pipeline.py --dry-run --mode auto --niche "finanzas personales"
python scripts/run_viral_pipeline.py --dry-run --mode motor_a --niche "finanzas personales"
python scripts/run_viral_pipeline.py --dry-run --mode motor_b --niche "finanzas personales"
```

## Salidas
- JSON principal: `output_test/viral_system/last_run.json`
- Artefactos temporales: `viral_video_system/temp/`

## Notas de compatibilidad
- No se sustituyó ningún flujo de producción existente.
- El nuevo sistema usa fallbacks para seguir funcionando sin `ollama`, `edge-tts` o `pytrends`.
- Para modo real, instala `requirements_viral_system.txt` y habilita servicios opcionales en `docker-compose`.

## Activacion por feature flag (worker actual)
El worker puede usar el bridge sin cambiar tu API ni colas actuales.

Variables:
- `USE_VIRAL_SYSTEM=1`: activa `app/scripts/ingest_viral_bridge.py`.
- `VIRAL_PIPELINE_MODE=auto|motor_a|motor_b`: seleccion de motor.
- `VIRAL_PIPELINE_DRY_RUN=1|0`: dry-run del pipeline nuevo.
- `VIRAL_BRIDGE_ONLY=1|0`: para pruebas (si 1, no ejecuta `ingest.py` legacy).

Ejemplo en PowerShell (prueba segura):
```powershell
$env:USE_VIRAL_SYSTEM='1'
$env:VIRAL_PIPELINE_MODE='auto'
$env:VIRAL_PIPELINE_DRY_RUN='1'
$env:VIRAL_BRIDGE_ONLY='1'
python app/scripts/ingest_viral_bridge.py 00000000-0000-0000-0000-000000000000 "https://youtu.be/dQw4w9WgXcQ"
```
