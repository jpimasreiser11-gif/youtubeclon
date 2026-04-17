#!/usr/bin/env python3
"""
Generador del Calendario de Prompts de 365 días para VidFlow AI.
Cada día del año, cada agente tiene una tarea diferente y específica.
El objetivo: que el sistema mejore continuamente y nunca repita exactamente lo mismo.

Uso: python scripts/generate_calendar.py
Genera: .openclaw/calendar/prompt_calendar.json
        .openclaw/calendar/calendar_human_readable.md
"""

import json
from datetime import date, timedelta
from pathlib import Path

# ─── ESTRUCTURA DE TEMAS POR SEMANA ────────────────────────────────────────
# El año se divide en 52 semanas con 7 focos temáticos rotativos

WEEKLY_THEMES = [
    # Q1 — Fundación y primeros ingresos (semanas 1-13)
    {"week": 1,  "theme": "Fundación del sistema",      "focus": "Verificar que todo funciona, configurar lo que falta, primeras métricas"},
    {"week": 2,  "theme": "Primeros afiliados",          "focus": "Activar Amazon Associates + Impact.com para todos los canales"},
    {"week": 3,  "theme": "Optimización de hooks",       "focus": "Mejorar los primeros 3 segundos de todos los vídeos basándose en retención"},
    {"week": 4,  "theme": "SEO profundo",                "focus": "Auditar y mejorar todos los títulos y descripciones publicados"},
    {"week": 5,  "theme": "Análisis de competidores",   "focus": "Estudiar los 3 mejores canales de cada nicho — qué hacen diferente"},
    {"week": 6,  "theme": "Thumbnails y CTR",            "focus": "Rediseñar thumbnails, medir CTR antes/después"},
    {"week": 7,  "theme": "Voice y audio",               "focus": "Probar nuevas voces, medir retención de audio"},
    {"week": 8,  "theme": "Primeros $10",                "focus": "Primer informe real de ingresos, qué está convirtiendo"},
    {"week": 9,  "theme": "Shorts y TikTok",             "focus": "Optimizar el formato corto, encontrar el gancho vertical"},
    {"week": 10, "theme": "Keywords long-tail",          "focus": "Buscar keywords con menos competencia pero volumen real"},
    {"week": 11, "theme": "Engagement y comentarios",   "focus": "Activar comunidad, responder comentarios, crear conversación"},
    {"week": 12, "theme": "Pitch para sponsors",         "focus": "Crear el media kit, identificar primeras marcas a contactar"},
    {"week": 13, "theme": "Q1 Retrospectiva",            "focus": "Qué funcionó, qué no, ajustar estrategia para Q2"},

    # Q2 — Escala y monetización (semanas 14-26)
    {"week": 14, "theme": "Escala de producción",        "focus": "Aumentar a 2 vídeos/día en los 2 canales con mejor tracción"},
    {"week": 15, "theme": "Nuevos afiliados",            "focus": "Añadir Brilliant.org, Masterworks según niche"},
    {"week": 16, "theme": "Email capture",               "focus": "Crear lead magnet por canal, primera secuencia de bienvenida"},
    {"week": 17, "theme": "Producto digital #1",         "focus": "Definir y empaquetar el primer ebook/template por canal top"},
    {"week": 18, "theme": "Virality experiment",         "focus": "Probar el formato más viral — mystery, shocking stat, countdown"},
    {"week": 19, "theme": "Cross-promotion interna",    "focus": "Los 6 canales se promueven entre sí de forma estratégica"},
    {"week": 20, "theme": "Análisis de retención",       "focus": "Identificar en qué minuto exacto la gente se va y por qué"},
    {"week": 21, "theme": "Primer $100",                 "focus": "Sprint para llegar a $100 de ingresos — qué falta, qué acelerar"},
    {"week": 22, "theme": "Outreach a sponsors",         "focus": "Enviar 10 emails de propuesta de patrocinio por canal maduro"},
    {"week": 23, "theme": "A/B testing masivo",          "focus": "Probar 3 títulos por vídeo durante 2 semanas"},
    {"week": 24, "theme": "Community building",          "focus": "Crear Discord o Telegram por canal con más suscriptores"},
    {"week": 25, "theme": "Nuevo nicho exploration",    "focus": "Investigar si hay un 7° nicho sin explotar de alta RPM"},
    {"week": 26, "theme": "Q2 Retrospectiva",            "focus": "Midyear review — ingresos reales vs proyectados"},

    # Q3 — Diversificación (semanas 27-39)
    {"week": 27, "theme": "LinkedIn expansion",          "focus": "Adaptar contenido de IA/finanzas para LinkedIn"},
    {"week": 28, "theme": "Productos digitales escala",  "focus": "Lanzar el segundo producto digital — mini-curso"},
    {"week": 29, "theme": "Automatización avanzada",    "focus": "Mejorar el pipeline para reducir intervención humana al mínimo"},
    {"week": 30, "theme": "Testimonios y social proof",  "focus": "Recopilar primeros resultados reales para usar en contenido"},
    {"week": 31, "theme": "Newsletter monetización",    "focus": "Primera campaña de email con oferta de afiliado"},
    {"week": 32, "theme": "System Seller prep",          "focus": "Documentar el sistema para venderlo como producto"},
    {"week": 33, "theme": "Nuevas herramientas IA",      "focus": "Integrar las mejores herramientas gratuitas lanzadas en Q3"},
    {"week": 34, "theme": "Primer sponsor cerrado",      "focus": "Sprint para cerrar el primer patrocinio pagado"},
    {"week": 35, "theme": "Canales inglés vs español",   "focus": "Comparar RPM y escalar el tipo de canal más rentable"},
    {"week": 36, "theme": "Optimización de costes",      "focus": "Revisar qué APIs se pueden sustituir por alternativas más baratas"},
    {"week": 37, "theme": "Contenido evergreen",         "focus": "Crear vídeos que seguirán generando vistas en 2 años"},
    {"week": 38, "theme": "Milestone $500/mes",          "focus": "Plan específico para llegar a $500/mes"},
    {"week": 39, "theme": "Q3 Retrospectiva",            "focus": "¿Qué cambiaría si empezara de nuevo hoy?"},

    # Q4 — Escala máxima (semanas 40-52)
    {"week": 40, "theme": "Navidad/Q4 prep",             "focus": "Q4 tiene CPM 30-50% más alto — maximizar producción en octubre"},
    {"week": 41, "theme": "Colaboraciones",              "focus": "Identificar creadores afines para colaboraciones"},
    {"week": 42, "theme": "2° canal por nicho",          "focus": "Si un canal funciona bien, crear variante para captar más audiencia"},
    {"week": 43, "theme": "Traducción de contenido",     "focus": "Traducir los mejores vídeos al idioma opuesto (ES→EN o EN→ES)"},
    {"week": 44, "theme": "Black Friday sprint",         "focus": "Maximizar ingresos de afiliados durante el período de mayor compra"},
    {"week": 45, "theme": "Sistema vendible",            "focus": "Crear landing page del sistema como producto para vender"},
    {"week": 46, "theme": "Media kit actualizado",       "focus": "Actualizar stats y redesign del media kit con datos reales"},
    {"week": 47, "theme": "Patrocinios Q1 siguiente",   "focus": "Cerrar acuerdos de patrocinio para enero-marzo"},
    {"week": 48, "theme": "Milestone $1.000/mes",        "focus": "¿Cuánto falta? Plan sprint final del año"},
    {"week": 49, "theme": "Diciembre: evergreen push",  "focus": "Publicar contenido que funcionará bien en enero"},
    {"week": 50, "theme": "Año review",                  "focus": "Informe anual completo — ingresos reales, lecciones, mejores vídeos"},
    {"week": 51, "theme": "Plan Q1 siguiente año",       "focus": "Definir la estrategia exacta para el siguiente año"},
    {"week": 52, "theme": "Celebrar y descansar",        "focus": "El sistema sigue solo. Tú miras los resultados y descansas."},
]

# ─── TAREAS DIARIAS POR AGENTE ────────────────────────────────────────────
# Cada agente tiene un conjunto de tareas rotativas
# El día del año (1-365) determina qué tarea toca

AGENT_DAILY_TASKS = {
    "00-patriarch": [
        "Leer todos los diarios de agentes del día anterior y escribir un análisis de 300 palabras sobre el progreso del sistema. Identificar el mayor logro y el mayor problema.",
        "Revisar el roadmap de ingresos. ¿Estamos en el camino correcto? Proponer 1 ajuste de estrategia basado en los datos de esta semana.",
        "Leer los últimos 30 cambios del changelog y evaluar: ¿los agentes están trabajando en las cosas más importantes para generar ingresos?",
        "Escribir un memo para todo el equipo sobre las prioridades de la próxima semana. Distribuirlo en shared-memory/team_updates.md.",
        "Revisar NEEDS_FROM_HUMAN.md y priorizar las peticiones por impacto en ingresos. Marcar las que son realmente urgentes.",
        "Evaluar el estado de cada canal: ¿cuál tiene más potencial ahora mismo? Reasignar recursos de los agentes si es necesario.",
        "Buscar en internet casos de éxito de canales faceless en los mismos nichos. ¿Qué hacen que nosotros no hacemos?",
    ],
    "01-researcher": [
        "Analizar los 5 vídeos más vistos de esta semana en cada uno de los 6 nichos. Documentar: título exacto, duración, thumbnail description, estructura narrativa.",
        "Buscar cambios de algoritmo de YouTube en los últimos 14 días. Fuentes: Creator Insider, VidIQ blog, TubeBuddy blog.",
        "Investigar los programas de afiliados más rentables actualmente para el nicho de finanzas. Comparar CPA, cookie duration, conversion rate.",
        "Estudiar a los 3 competidores más directos de Wealth Files. ¿Cuántos suscriptores ganan por mes? ¿Qué tipo de vídeos funcionan mejor?",
        "Buscar estudios académicos o informes sobre comportamiento del consumidor relacionados con los nichos del proyecto.",
        "Analizar qué temas de cada nicho NO están siendo cubiertos por la competencia. Documentar los gaps de contenido.",
        "Rastrear las últimas noticias relevantes para los 6 nichos. Identificar qué eventos actuales tienen potencial de contenido.",
    ],
    "02-content-forge": [
        "Generar 3 guiones completos con estructura anti-ban. Uno para Impacto Mundial, uno para Mind Warp, uno para Dark Science.",
        "Crear 6 scripts de TikTok autónomos (uno por canal). Cada uno debe ser 100% independiente del vídeo largo correspondiente.",
        "Mejorar los hooks de los últimos 5 guiones basándose en el feedback de retención. Reescribir solo los primeros 20 segundos de cada uno.",
        "Crear 2 guiones para El Loco de la IA sobre las herramientas gratuitas más populares del momento.",
        "Desarrollar una serie de 3 partes para Mentes Rotas sobre un caso real de psicología criminal. Planificar la narrativa arco de las 3 entregas.",
        "Generar variantes de CTA para cada canal. Probar 3 formulaciones diferentes que sean específicas y no genéricas.",
        "Crear 3 guiones tipo 'documental corto' para Wealth Files (12-15 min) sobre imperios financieros caídos.",
    ],
    "09-trend-hunter": [
        "Escanear Google Trends para todos los nichos. Buscar tendencias 'Breakout' (>5000% de incremento). Documentar y notificar urgente si hay alguna.",
        "Revisar las 20 publicaciones más upvoteadas de esta semana en r/finance, r/psychology, r/space, r/ChatGPT, r/truecrime.",
        "Monitorizar YouTube Trending por categoría (Education, Science, Entertainment). Identificar patrones de formato que se repiten.",
        "Buscar en Twitter/X qué temas de nuestros nichos están siendo discutidos en tiempo real. Usar la búsqueda avanzada por fecha.",
        "Revisar newsletters especializadas de cada nicho (Morning Brew para finanzas, AI Weekly para IA). Identificar temas emergentes.",
        "Analizar qué vídeos de la competencia tuvieron un pico de views inesperado esta semana. Investigar por qué.",
        "Estudiar qué hashtags de TikTok en los nichos del proyecto tienen más vistas esta semana vs la semana pasada.",
    ],
    "04-seo-engineer": [
        "Auditar todos los títulos publicados en la última semana. Calcular CTR estimado para cada uno y proponer mejoras.",
        "Investigar las keywords de cola larga más buscadas en cada nicho usando Google Search Console (si hay acceso) o VidIQ.",
        "Optimizar las descripciones de los 10 vídeos con menos views del mes. Añadir timestamps, CTAs y keywords faltantes.",
        "Crear variantes de thumbnails para los 3 vídeos con peor CTR. Describir el concepto visual para que el generador de thumbnails lo implemente.",
        "Analizar el comportamiento de búsqueda: qué busca la gente en YouTube que lleva a nuestros vídeos vs nuestros competidores.",
        "Optimizar los metadatos de cada canal: descripción del canal, keywords, enlaces en about. Comparar con los mejores canales del nicho.",
        "Crear una guía actualizada de mejores prácticas de SEO para YouTube basada en datos del mes actual.",
    ],
    "06-money-finder": [
        "Revisar todos los links de afiliados activos. ¿Están funcionando? ¿Han cambiado las comisiones? ¿Hay mejores alternativas?",
        "Buscar en Impact.com y ShareASale nuevos programas de afiliados en los nichos del proyecto lanzados en los últimos 30 días.",
        "Calcular el ingreso estimado de afiliados por canal basándose en views × CTR estimado × tasa de conversión típica del nicho.",
        "Identificar qué vídeos tienen el mayor potencial de conversión de afiliados y proponer cómo mencionarlos más naturalmente.",
        "Investigar los precios de mercado para sponsorships en canales del mismo tamaño. Actualizar el media kit con estos datos.",
        "Buscar activamente marcas pequeñas en los nichos que estén invirtiendo en influencer marketing. Crear una lista de prospección.",
        "Evaluar si algún contenido existente puede transformarse en un producto digital vendible (ebook, template, checklist).",
    ],
    "07-data-analyst": [
        "Leer todos los datos disponibles de la semana y producir el scorecard de cada canal (0-100 puntos, basado en 5 métricas).",
        "Comparar el rendimiento de esta semana con la semana anterior. Identificar qué cambió y por qué.",
        "Analizar qué tipo de contenido (mystery, countdown, case study, tutorial) tiene mejor retención por canal.",
        "Calcular el ingreso estimado mensual actual y proyección a 3 meses si se mantiene el ritmo.",
        "Identificar anomalías: ¿hay algún vídeo que está funcionando mucho mejor o mucho peor de lo esperado? Investigar por qué.",
        "Revisar el quality score histórico de Agent-05. ¿Está mejorando? ¿Qué tipo de problemas siguen apareciendo?",
        "Crear el informe semanal completo con gráficas textuales de progreso y recomendaciones para la siguiente semana.",
    ],
    "03-code-sentinel": [
        "Revisar pipeline.py completo buscando funciones sin manejo de errores. Añadir try/except donde falte.",
        "Verificar que todos los imports del proyecto están en requirements.txt. Instalar los que falten.",
        "Revisar el tiempo de ejecución del pipeline completo. Identificar el paso más lento y proponer optimización.",
        "Auditar todo el código en busca de credenciales hardcodeadas. Moverlas a .env si se encuentran.",
        "Escribir tests para los módulos más críticos: downloader_footage, ensamblador_pro, youtube_uploader.",
        "Revisar que la lógica de retry en todas las llamadas API es correcta y consistente.",
        "Documentar las funciones principales del pipeline con docstrings en español.",
    ],
    "08-fixer": [
        "Revisar los últimos 100 líneas de todos los logs. Identificar patrones de error repetitivos.",
        "Verificar que todos los tokens OAuth están activos. Refrescarlos automáticamente si es posible.",
        "Comprobar que todas las APIs responden correctamente. Ejecutar check_apis.py y documentar resultados.",
        "Revisar pipeline_queue.json. Limpiar entradas antiguas con status FAILED o UPLOADED de hace más de 7 días.",
        "Verificar que el espacio en disco es suficiente. Limpiar archivos temporales si el disco supera el 80% de uso.",
        "Comprobar que GitHub Actions corrió correctamente ayer. Revisar el workflow run y corregir si falló.",
        "Revisar los diarios de todos los agentes buscando menciones de errores o problemas que aún no se hayan resuelto.",
    ],
    "05-quality-gate": [
        "Revisar los últimos 10 vídeos aprobados. ¿Pasaron todos los checks correctamente? ¿Hay algún falso positivo?",
        "Actualizar los thresholds de los checks basándose en los resultados de la semana. ¿Algún check es demasiado estricto o demasiado lento?",
        "Revisar los 3 últimos vídeos rechazados. ¿Los motivos de rechazo eran válidos? ¿Se corrigieron bien?",
        "Evaluar si el check de voz naturalidad (Check 2) está calibrado correctamente basándose en feedback de retención real.",
        "Proponer un nuevo check basándose en patrones de baja retención detectados esta semana.",
        "Revisar que Agent-25 (Video Quality Verifier) está aplicando bien los checks subjetivos.",
        "Crear un informe mensual de quality score promedio por canal con tendencia histórica.",
    ],
    "24-net-forager": [
        "Buscar en GitHub repositorios con >100 stars de la semana pasada relacionados con: video automation, youtube tools, tts, ai content.",
        "Revisar Product Hunt de esta semana. Identificar las 3 herramientas gratuitas o freemium más útiles para el proyecto.",
        "Leer HackerNews frontpage y Show HN. Documentar cualquier post relevante para los nichos o el pipeline.",
        "Buscar estudios de caso de canales YouTube que pasaron de 0 a monetización en menos de 3 meses. Extraer lecciones concretas.",
        "Recopilar TODOS los NEEDS_FROM_HUMAN de todos los agentes en un solo documento priorizado. Presentarlo de forma clara.",
        "Buscar mejoras de herramientas que ya usamos: ¿ElevenLabs lanzó nuevas voces? ¿Pexels tiene nuevas categorías? ¿ffmpeg tiene nuevas funciones?",
        "Identificar comunidades online (Reddit, Discord, forums) donde se discutan nuestros nichos. Documentar para que Community (Agent-21) las monitorice.",
    ],
    "25-video-quality": [
        "Ver 3 vídeos de competidores top en cada nicho. Documentar: hook, ritmo de edición, uso de música, estilo de subtítulos.",
        "Buscar estudios nuevos sobre retención en YouTube. Implementar cualquier técnica con evidencia sólida.",
        "Probar una voz diferente en un vídeo de prueba para cada canal. Comparar naturalidad con la voz actual.",
        "Analizar los vídeos del proyecto con mejor retención (>65%). ¿Qué tienen en común? ¿Cómo replicarlo sistemáticamente?",
        "Evaluar los últimos 5 vídeos con la nueva herramienta de generación de vídeo si se ha implementado alguna.",
        "Revisar los clips visuales de los últimos vídeos: ¿son todos relevantes? ¿Hay clips genéricos que se repiten demasiado?",
        "Buscar en ClawHub o GitHub nuevas skills de edición de vídeo que puedan mejorar la calidad del output final.",
    ],
    "11-ui-evolution": [
        "Revisar el dashboard visual (office/index.html). Identificar qué información falta o es difícil de encontrar.",
        "Mejorar el sistema de notificaciones: ¿llegan a tiempo? ¿Son claras? ¿Hay demasiado ruido?",
        "Añadir al dashboard una vista de 'ingresos en tiempo real' con los datos de income_tracker.json.",
        "Crear una vista de calendario en el dashboard que muestre los vídeos programados para los próximos 7 días.",
        "Optimizar la versión móvil del dashboard para poder consultarlo desde el teléfono cómodamente.",
        "Añadir gráficas de progreso de suscriptores por canal (aunque sean estimadas si no hay datos reales aún).",
        "Revisar y mejorar la interfaz de chat individual con cada agente en el panel lateral del dashboard.",
    ],
    "12-performance": [
        "Medir el tiempo de ejecución de cada paso del pipeline. Documentar los tiempos en performance_log.json.",
        "Identificar el cuello de botella principal del pipeline. Proponer e implementar una mejora.",
        "Revisar el uso de memoria durante la ejecución del pipeline. Identificar fugas de memoria si las hay.",
        "Optimizar las llamadas a la API de Pexels: ¿se pueden hacer en paralelo? ¿Hay exceso de requests?",
        "Revisar los logs de GitHub Actions. ¿Los workflows están dentro de los 2.000 minutos gratuitos del mes?",
        "Probar si el pipeline es más rápido con asyncio en lugar de requests síncrono en las llamadas de descarga.",
        "Crear un benchmark semanal: tiempo promedio desde guión hasta vídeo listo. Reducir este tiempo cada semana.",
    ],
    "18-shorts": [
        "Generar 6 scripts de Shorts/TikTok únicos (uno por canal) siguiendo la estructura: hook 2s + valor 45s + CTA 5s.",
        "Analizar qué Shorts de la competencia en cada nicho tienen más de 1M de views. ¿Qué tienen en común?",
        "Mejorar el módulo de corte automático (tiktok_clipper.py). Identificar el minuto más impactante del vídeo de forma más inteligente.",
        "Probar diferentes formatos de subtítulos para los Shorts: tamaño, posición, animación, colores por canal.",
        "Estudiar qué música de tendencia en TikTok encaja con cada canal y documentarlo para su uso.",
        "Crear una plantilla de guión específica para Shorts de 30 segundos (más cortos que los de 60-90s habituales).",
        "Analizar la retención de los Shorts del proyecto si hay datos. ¿En qué segundo exacto se va más gente?",
    ],
    "19-distribution": [
        "Verificar que todos los vídeos de la semana se publicaron en todos los canales programados.",
        "Revisar las mejores horas de publicación para cada plataforma basándose en los datos de engagement de la semana.",
        "Crear las leyendas y hashtags optimizados para Instagram Reels de los 3 mejores vídeos de la semana.",
        "Actualizar el calendario de distribución para la semana siguiente con los horarios optimizados.",
        "Revisar si hay vídeos evergreen del pasado que puedan republucarse o compartirse de nuevo.",
        "Estudiar qué funciona en LinkedIn para los nichos de IA y finanzas. Adaptar 1 pieza de contenido para probar.",
        "Asegurarse de que los links entre plataformas (YouTube → TikTok → newsletter) están activos y correctos.",
    ],
    "13-adsense-web": [
        "Analizar el RPM de cada canal por tipo de contenido. ¿Qué topics tienen mayor CPM?",
        "Investigar las mejores horas de publicación para maximizar CPM (varía según audiencia y temporada).",
        "Revisar la duración óptima para activar el máximo de mid-rolls sin afectar la retención.",
        "Estudiar qué canales del nicho tienen el mayor RPM declarado y qué tipo de contenido producen.",
        "Calcular la proyección de ingresos de AdSense para el mes actual basándose en views × RPM estimado.",
        "Analizar si Q4 ya está mostrando el incremento de CPM del 30-50% esperado. Ajustar estrategia si procede.",
        "Revisar si hay vídeos marcados como 'no apto para anunciantes' y proponer cómo hacerlos aptos.",
    ],
    "14-affiliate": [
        "Verificar que TODOS los links de afiliados en todas las descripciones de todos los canales están activos.",
        "Calcular el ingreso estimado de afiliados de esta semana por programa y por canal.",
        "Identificar qué vídeos tienen alto tráfico pero poca conversión de afiliados. Proponer cómo mejorar el placement.",
        "Buscar 1 nuevo programa de afiliados con CPA > $20 que encaje perfectamente con algún canal.",
        "Revisar las comisiones de todos los programas activos. ¿Ha cambiado alguna? ¿Hay que negociar mejor condiciones?",
        "Crear el plan de afiliados para los próximos vídeos programados. Asignar el afiliado más relevante a cada tema.",
        "Analizar el ratio clicks/conversiones por afiliado. Identificar cuáles no convierten y reemplazarlos.",
    ],
    "15-digital-products": [
        "Evaluar qué contenido existente tiene el potencial más alto de convertirse en un producto digital vendible.",
        "Bosquejar la estructura del próximo ebook/template. ¿Qué promesa tiene? ¿Qué problema resuelve?",
        "Investigar qué productos digitales se venden bien en Gumroad en los nichos del proyecto y a qué precio.",
        "Crear la landing page mínima para el primer producto digital usando HTML simple.",
        "Definir la secuencia de email de lanzamiento del producto (3 emails: anticipación, lanzamiento, recordatorio).",
        "Analizar si hay suficiente audiencia para lanzar el primer producto. ¿Cuántos suscriptores mínimos se necesitan?",
        "Crear el brief de diseño del primer producto: portada, nombre, precio, descripción de 50 palabras.",
    ],
    "16-sponsorship": [
        "Actualizar el media kit con los datos más recientes de todos los canales.",
        "Identificar 5 marcas nuevas que estarían bien alineadas con los canales más grandes.",
        "Revisar el pipeline de sponsorships: qué marcas están en prospección, contactadas, en negociación.",
        "Investigar las tarifas de mercado actuales para sponsorships en canales del mismo tamaño que los nuestros.",
        "Escribir un email de outreach personalizado para la marca con más fit de la semana.",
        "Crear un caso de estudio de cómo el contenido del canal ayudaría a la marca a llegar a su audiencia objetivo.",
        "Estudiar cómo los creadores top de cada nicho presentan sus sponsors de forma no intrusiva.",
    ],
    "17-newsletter": [
        "Crear el lead magnet de esta semana para el canal con más suscriptores (un recurso descargable relacionado con el mejor vídeo).",
        "Escribir el email de valor de esta semana para la lista (resumen de lo más interesante de los vídeos publicados).",
        "Analizar las métricas de los últimos emails enviados: open rate, click rate, conversiones.",
        "Mejorar el asunto de los próximos emails basándose en qué asuntos han funcionado mejor.",
        "Crear una secuencia automática de bienvenida de 3 emails para nuevos suscriptores.",
        "Identificar qué contenido del canal tiene más potencial para convertirse en email exclusivo para la lista.",
        "Investigar herramientas gratuitas de email marketing que permitan al menos 1.000 suscriptores sin coste.",
    ],
    "20-system-seller": [
        "Documentar el sistema VidFlow como si fuera un producto vendible. ¿Qué problema resuelve? ¿Quién lo compraría?",
        "Investigar en qué plataformas (Gumroad, Etsy, AppSumo) se venden sistemas de automatización similares y a qué precio.",
        "Crear la propuesta de valor del sistema: ¿qué lo diferencia de lo que ya existe en el mercado?",
        "Escribir el primer testimonio hipotético: ¿qué diría alguien que usó el sistema y funcionó?",
        "Bosquejar un tutorial de vídeo que explique el sistema. Esto serviría como contenido para El Loco de la IA Y como demostración del producto.",
        "Calcular el precio óptimo del sistema como producto: ¿$49? ¿$97? ¿$297? Investigar la competencia.",
        "Crear un README comercial del sistema que sirva como carta de ventas técnica.",
    ],
    "21-community": [
        "Revisar los comentarios de los últimos 7 días en todos los canales de YouTube. Responder a los más relevantes.",
        "Identificar los 3 comentarios más frecuentes o preguntas recurrentes por canal. Usarlos como ideas de vídeo.",
        "Crear 3 preguntas de engagement para añadir al final de los guiones de la semana siguiente.",
        "Buscar comunidades online (Reddit, Discord, Quora) donde se discutan nuestros nichos. Documentarlas.",
        "Diseñar una encuesta rápida de 3 preguntas para saber qué contenido quiere más la audiencia.",
        "Analizar el ratio engagement/views del canal con mejor communidad. ¿Qué hace diferente?",
        "Crear un plan de community building para el canal con menos engagement. Qué acciones específicas tomará.",
    ],
    "22-ab-testing": [
        "Diseñar un test A/B de títulos para los 3 próximos vídeos del canal con más views.",
        "Revisar los resultados de los tests activos de la semana anterior. ¿Qué variante ganó? ¿Con qué margen?",
        "Definir la hipótesis del próximo test de thumbnail: ¿texto vs no texto? ¿cara vs no cara? ¿fondo oscuro vs claro?",
        "Calcular qué tamaño de muestra se necesita para que un test sea estadísticamente significativo con nuestro volumen.",
        "Crear el plan de tests para el mes siguiente: qué variable probar, en qué canal, durante cuánto tiempo.",
        "Documentar los aprendizajes acumulados de todos los tests. ¿Qué patrón emerge?",
        "Compartir los hallazgos de esta semana con Agent-04 (SEO) y Agent-02 (Content) para implementarlos.",
    ],
    "23-virality": [
        "Analizar los 10 vídeos más compartidos de esta semana en los nichos del proyecto. ¿Qué tienen en común?",
        "Evaluar el 'factor viral' de los guiones planificados para mañana. Dar una nota del 1-10 y mejorar los que estén por debajo de 7.",
        "Identificar el 'momento emotivo' de cada guión de la semana: ¿hay un momento que la gente compartirá?",
        "Estudiar cómo los vídeos virales en nuestros nichos estructuran los primeros 3 segundos.",
        "Crear un banco de 20 hooks de alta viralidad específicos para cada canal del proyecto.",
        "Revisar si el sistema de open loops (preguntas sin responder) está siendo usado correctamente en todos los guiones.",
        "Proponer una estructura narrativa nueva basada en los patrones virales más exitosos de la semana.",
    ],
    "10-scheduler": [
        "Revisar el calendario de publicaciones de la próxima semana. ¿Hay huecos? ¿Están balanceados los canales?",
        "Actualizar la prioridad de los agentes para hoy basándose en qué tarea tiene mayor impacto en ingresos.",
        "Verificar que el cron job de GitHub Actions funcionó correctamente ayer. Si no, diagnosticar y reprogramar.",
        "Revisar si hay vídeos en pipeline_queue.json que llevan más de 48h en estado PENDING. Escalar a Agent-08.",
        "Crear el plan de publicaciones de la semana siguiente con horarios optimizados por plataforma.",
        "Coordinar con Agent-00 (Patriarch) si hay cambios de prioridad para esta semana.",
        "Verificar que el heartbeat de todos los agentes en OpenClaw está configurado correctamente.",
    ],
}

def get_task_for_day(agent_id: str, day_of_year: int) -> str:
    """Obtiene la tarea específica para un agente en un día del año."""
    tasks = AGENT_DAILY_TASKS.get(agent_id, ["Revisa el sistema y propone mejoras."])
    task_idx = (day_of_year - 1) % len(tasks)
    return tasks[task_idx]

def get_weekly_theme(day_of_year: int) -> dict:
    """Obtiene el tema de la semana para un día del año."""
    week_num = ((day_of_year - 1) // 7) + 1
    week_num = min(week_num, 52)
    return next((t for t in WEEKLY_THEMES if t["week"] == week_num), WEEKLY_THEMES[-1])

def generate_day_prompt(day_of_year: int, date_str: str) -> dict:
    """Genera el prompt completo para un día específico del año."""
    theme = get_weekly_theme(day_of_year)
    
    agent_tasks = {}
    for agent_id in AGENT_DAILY_TASKS.keys():
        agent_tasks[agent_id] = get_task_for_day(agent_id, day_of_year)
    
    return {
        "day": day_of_year,
        "date": date_str,
        "week_theme": theme["theme"],
        "week_focus": theme["focus"],
        "agent_tasks": agent_tasks,
        "morning_briefing_prompt": f"""
Es el día {day_of_year} del año. Tema de esta semana: {theme['theme']}.
Focus: {theme['focus']}.

Lee todos los archivos de contexto relevantes para tu agente.
Ejecuta la tarea del día: {agent_tasks.get('00-patriarch', 'Coordinar el equipo')}.
Al terminar, actualiza tu memory.json y escribe en tu diario.
""",
    }

def generate_full_calendar():
    """Genera el calendario completo de 365 días."""
    calendar = []
    start_date = date(2025, 1, 1)
    
    for day in range(1, 366):
        current_date = start_date + timedelta(days=day-1)
        day_data = generate_day_prompt(day, current_date.isoformat())
        calendar.append(day_data)
    
    return calendar

def save_calendar(calendar: list):
    """Guarda el calendario en JSON y en formato legible."""
    output_dir = Path(".openclaw/calendar")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # JSON para el sistema
    json_file = output_dir / "prompt_calendar.json"
    json_file.write_text(json.dumps(calendar, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Calendario JSON: {json_file}")
    
    # Markdown para lectura humana
    md_file = output_dir / "calendar_human_readable.md"
    lines = ["# Calendario de Prompts VidFlow AI — 365 días\n\n"]
    
    current_week = None
    for day in calendar[:30]:  # Primeros 30 días como ejemplo
        if day["week_theme"] != current_week:
            current_week = day["week_theme"]
            lines.append(f"\n## Semana: {current_week}\n")
            lines.append(f"*{day['week_focus']}*\n\n")
        
        lines.append(f"### Día {day['day']} — {day['date']}\n")
        for agent_id, task in list(day["agent_tasks"].items())[:5]:  # 5 agentes como muestra
            lines.append(f"- **{agent_id}**: {task[:100]}...\n")
        lines.append("\n")
    
    lines.append("\n*[... y así para los 365 días del año]*\n")
    md_file.write_text("".join(lines), encoding="utf-8")
    print(f"✅ Calendario legible: {md_file}")

def get_today_prompt():
    """Obtiene el prompt del día actual."""
    today = date.today()
    day_of_year = today.timetuple().tm_yday
    return generate_day_prompt(day_of_year, today.isoformat())

if __name__ == "__main__":
    import sys
    
    if "--today" in sys.argv:
        prompt = get_today_prompt()
        print(f"\n📅 Día {prompt['day']} — {prompt['date']}")
        print(f"🎯 Tema: {prompt['week_theme']}")
        print(f"📌 Focus: {prompt['week_focus']}")
        print("\nTareas de hoy por agente:")
        for agent_id, task in prompt["agent_tasks"].items():
            print(f"\n  [{agent_id}]")
            print(f"  {task}")
    else:
        print("Generando calendario de 365 días...")
        calendar = generate_full_calendar()
        save_calendar(calendar)
        print(f"\n✅ Calendario generado: {len(calendar)} días")
        print("\nPara ver las tareas de hoy:")
        print("  python scripts/generate_calendar.py --today")
