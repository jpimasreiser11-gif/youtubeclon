# Runbook de Migracion Segura

## Fase 1 (actual)
- Arquitectura nueva en paralelo.
- Ejecucion por bridge script.
- Dry-run validado.

## Fase 2
- Conectar `viral_video_system.pipeline` desde worker existente por feature flag.
- Escribir resultados en tablas actuales (`projects`, `clips`) sin romper API frontend.

## Fase 3
- Activar n8n + ollama via perfiles de docker compose.
- Mover cron jobs a n8n nodo a nodo.

## Feature flag sugerido
- `USE_VIRAL_SYSTEM=true` para enrutar job processing al nuevo pipeline.
