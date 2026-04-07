# Analytics Tracking Plan

Last updated: 2026-04-07

## Stack
- Captura frontend: `trackEvent()` en app web
- Destinos compatibles: `window.gtag` (GA4) y `window.dataLayer` (GTM)
- Estado actual: eventos ya instrumentados en Home, Motor B y ClipRadar

## Eventos Instrumentados (ya aplicados)

| Event Name | Trigger | Key Properties |
|---|---|---|
| motor_a_metadata_requested | Solicitud metadata en Home | has_url |
| motor_a_metadata_loaded | Metadata recibida correctamente | has_thumbnail |
| motor_a_metadata_failed | Error metadata Home | - |
| motor_a_job_create_clicked | Click crear job Motor A (Home) | niche, has_url |
| motor_a_job_created | Job Motor A creado (Home) | job_id, niche |
| motor_a_job_create_failed | Error creando Motor A (Home) | niche |
| motor_b_job_create_clicked | Click crear job Motor B | niche, trend_mode, keywords_count, has_prebuilt_script |
| motor_b_job_created | Job Motor B creado | job_id, niche, trend_mode |
| motor_b_job_create_failed | Error creando Motor B | niche, trend_mode |
| clipradar_search_started | Inicio busqueda ClipRadar | lang, query |
| clipradar_search_completed | Fin busqueda ClipRadar | lang, query, results_count |
| clipradar_search_failed | Error busqueda ClipRadar | lang, query |
| clipradar_motor_a_job_create_clicked | Crear Motor A desde ClipRadar | source_url, niche |
| clipradar_motor_a_job_created | Job Motor A desde ClipRadar creado | job_id, niche |
| clipradar_motor_a_job_create_failed | Error Motor A desde ClipRadar | niche |

## Embudo Recomendado
1. `clipradar_search_started`
2. `clipradar_search_completed`
3. `clipradar_motor_a_job_create_clicked`
4. `clipradar_motor_a_job_created`
5. Project status `COMPLETED` (en DB)

Embudo Motor B:
1. `motor_b_job_create_clicked`
2. `motor_b_job_created`
3. Project status `COMPLETED` (en DB)

## KPIs para negocio
- Conversion a primer job creado (A o B)
- Tiempo medio de `job_created` a `COMPLETED`
- Ratio de error por motor (`*_failed` / `*_clicked`)
- Ratio de completitud por nicho

## Siguiente Iteracion (prioridad)
1. Enviar eventos de estado backend (`job_processing`, `job_completed`, `job_failed`) desde worker.
2. Persistir eventos en tabla analitica para dashboard interno.
3. Vincular eventos a plan/tier para analisis de monetizacion.
4. Crear panel de cohortes por canal de adquisicion (UTM).
