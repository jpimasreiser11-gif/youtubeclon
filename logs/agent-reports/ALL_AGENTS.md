# Reporte global de agentes

Actualizado: 2026-04-17 17:59:25

| Agente | Runs | OK | ERR | Ultima accion |
|---|---:|---:|---:|---|
| 00 - 00-patriarch | 2645 | 2645 | 0 | Write patriarch diary and status board | HOY: Revisar el roadmap de ingresos. ¿Estamos en el camino correcto? Proponer 1 ajuste de estrategia basado en los datos de esta semana. |
| 01 - 01-coordinator | 3304 | 3304 | 0 | Validate team config and agent registry | HOY: Buscar cambios de algoritmo de YouTube en los últimos 14 días. Fuentes: Creator Insider, VidIQ blog, TubeBuddy blog. |
| 02 - 02-research-trends | 3302 | 3302 | 0 | Scan trends dataset | HOY: Crear 6 scripts de TikTok autónomos (uno por canal). Cada uno debe ser 100% independiente del vídeo largo correspondiente. |
| 03 - 03-script-director | 3302 | 3302 | 0 | Inspect latest script quality source | HOY: Verificar que todos los imports del proyecto están en requirements.txt. Instalar los que falten. |
| 04 - 04-voice-audio | 3302 | 3302 | 0 | Check latest narration audio asset | HOY: Investigar las keywords de cola larga más buscadas en cada nicho usando Google Search Console (si hay acceso) o VidIQ. |
| 05 - 05-footage-curator | 3301 | 3301 | 0 | Count available B-roll clips | HOY: Actualizar los thresholds de los checks basándose en los resultados de la semana. ¿Algún check es demasiado estricto o demasiado lento? |
| 06 - 06-video-editor | 3300 | 3299 | 1 | Validate latest final video asset | HOY: Buscar en Impact.com y ShareASale nuevos programas de afiliados en los nichos del proyecto lanzados en los últimos 30 días. |
| 07 - 07-thumbnail-seo | 3297 | 3297 | 0 | Validate thumbnail and generate income report | HOY: Comparar el rendimiento de esta semana con la semana anterior. Identificar qué cambió y por qué. |
| 25 - 25-video-quality | 739 | 738 | 1 | Evaluate subjective video quality before QA Gate | HOY: Buscar estudios nuevos sobre retención en YouTube. Implementar cualquier técnica con evidencia sólida. |
| 08 - 08-qa-guardian | 3295 | 3295 | 0 | Run API smoke quality check | HOY: Verificar que todos los tokens OAuth están activos. Refrescarlos automáticamente si es posible. |
| 09 - 09-automation-ops | 3296 | 3296 | 0 | Check CI/CD workflow coverage | HOY: Revisar las 20 publicaciones más upvoteadas de esta semana en r/finance, r/psychology, r/space, r/ChatGPT, r/truecrime. |
| 24 - 24-net-forager | 2644 | 2644 | 0 | Scan internet improvements and assign tasks | HOY: Revisar Product Hunt de esta semana. Identificar las 3 herramientas gratuitas o freemium más útiles para el proyecto. |
| 10 - 10-growth-marketing | 3296 | 3296 | 0 | Check growth automation modules | HOY: Actualizar la prioridad de los agentes para hoy basándose en qué tarea tiene mayor impacto en ingresos. |
| 11 - 11-ui-evolution | 3277 | 3277 | 0 | Audit UI evolution surface | HOY: Mejorar el sistema de notificaciones: ¿llegan a tiempo? ¿Son claras? ¿Hay demasiado ruido? |
| 12 - 12-performance | 3277 | 3277 | 0 | Run performance smoke baseline | HOY: Identificar el cuello de botella principal del pipeline. Proponer e implementar una mejora. |
| 13 - 13-adsense-web | 3275 | 3275 | 0 | Review web monetization surfaces | HOY: Investigar las mejores horas de publicación para maximizar CPM (varía según audiencia y temporada). |
| 14 - 14-affiliate | 3275 | 3275 | 0 | Update affiliate opportunities tracker | HOY: Calcular el ingreso estimado de afiliados de esta semana por programa y por canal. |
| 15 - 15-digital-products | 3275 | 3275 | 0 | Maintain digital products roadmap | HOY: Bosquejar la estructura del próximo ebook/template. ¿Qué promesa tiene? ¿Qué problema resuelve? |
| 16 - 16-sponsorship | 3275 | 3275 | 0 | Track sponsorship outreach pipeline | HOY: Identificar 5 marcas nuevas que estarían bien alineadas con los canales más grandes. |
| 17 - 17-newsletter | 3275 | 3275 | 0 | Maintain newsletter growth plan | HOY: Escribir el email de valor de esta semana para la lista (resumen de lo más interesante de los vídeos publicados). |
| 18 - 18-shorts | 3275 | 3275 | 0 | Review shorts production inventory | HOY: Analizar qué Shorts de la competencia en cada nicho tienen más de 1M de views. ¿Qué tienen en común? |
| 19 - 19-distribution | 3275 | 3275 | 0 | Update distribution checklist | HOY: Revisar las mejores horas de publicación para cada plataforma basándose en los datos de engagement de la semana. |
| 20 - 20-system-seller | 3275 | 3275 | 0 | Refine system-offer positioning | HOY: Investigar en qué plataformas (Gumroad, Etsy, AppSumo) se venden sistemas de automatización similares y a qué precio. |
| 21 - 21-community | 3275 | 3275 | 0 | Maintain community growth playbook | HOY: Identificar los 3 comentarios más frecuentes o preguntas recurrentes por canal. Usarlos como ideas de vídeo. |
| 22 - 22-abtesting | 3275 | 3275 | 0 | Track A/B testing experiments | HOY: Revisar los resultados de los tests activos de la semana anterior. ¿Qué variante ganó? ¿Con qué margen? |
| 23 - 23-virality | 3275 | 3275 | 0 | Capture virality signal findings | HOY: Evaluar el 'factor viral' de los guiones planificados para mañana. Dar una nota del 1-10 y mejorar los que estén por debajo de 7. |

## Como ver todo en vivo
- Dashboard web: http://localhost:7700
- Estado terminal: python scripts\\agent_status.py
- Eventos globales: Get-Content logs\\agents-events.jsonl -Wait
- Progreso global: Get-Content logs\\agent-progress\\all-agents.progress.jsonl -Wait
