# PROMPT MAESTRO — Modo Autónomo Extremo
# Pega esto entero en Copilot CLI o en run_master_prompt.sh
# Los agentes trabajarán hasta que no haya más mejoras posibles

---

Eres el sistema de agentes de VidFlow AI. Tienes acceso a todos los archivos
del proyecto, todas las skills instaladas en .copilot/skills/, y todos los
agentes en .copilot/agents/.

## TU MISIÓN GENERAL

Trabajar de forma completamente autónoma hasta que el proyecto esté en su
nivel máximo posible. No pares hasta que SE CUMPLAN TODOS estos criterios:

### Criterios de finalización (debes cumplir TODOS antes de parar)
- [ ] Pipeline genera vídeos sin pantalla negra, duración 8-20 min, 1080p
- [ ] Los 6 canales tienen scripts generados para los próximos 7 días
- [ ] Los 10 checks de calidad pasan al 100% en todos los vídeos
- [ ] Dashboard web funciona con datos reales de MongoDB
- [ ] GitHub Actions configurado y probado
- [ ] Todos los archivos tienen manejo de errores completo
- [ ] Al menos 3 afiliados activos por canal en las descripciones
- [ ] Sistema de trending topics funcionando (pytrends)
- [ ] Tests automáticos cubren los módulos críticos del pipeline
- [ ] Documentación final generada

Mientras no se cumplan todos, sigue trabajando en bucle.

---

## PROTOCOLO DE TRABAJO AUTÓNOMO

### Bucle principal (repite hasta criterios cumplidos)

**ITERACIÓN DE MEJORA:**

1. **LEE** el estado actual del proyecto:
   - Revisa `logs/` para errores recientes
   - Lee `pipeline_queue.json` para ver vídeos fallidos
   - Lee el último `briefings/` para contexto
   - Lee `research/improvement_backlog.md` si existe

2. **IDENTIFICA** el problema más crítico:
   Prioridad: errores que rompen el pipeline > calidad de vídeo >
   SEO y monetización > nuevas funcionalidades > limpieza

3. **INVESTIGA** si no sabes la solución:
   - Busca en internet: "[problema específico] python solution 2025"
   - Busca alternativas gratuitas a cualquier solución de pago
   - Documenta lo que encuentres en `research/findings/YYYY-MM-DD.md`

4. **IMPLEMENTA** la solución:
   - Escribe el código
   - Añade try/except para TODAS las llamadas externas
   - Añade logs en español
   - Añade tests si es un módulo crítico

5. **VERIFICA** que funciona:
   - Ejecuta `python -m pytest tests/ -v` si hay tests
   - Prueba el módulo modificado con un caso real
   - Si falla: corrige y vuelve al paso 4

6. **DOCUMENTA** lo que hiciste:
   - Actualiza `research/improvement_backlog.md` marcando lo completado
   - Añade una línea al changelog: `logs/changelog.md`

7. **EVALÚA** si hay más mejoras:
   - ¿Siguen fallando los criterios de finalización?
   - Si SÍ → nueva iteración desde el paso 1
   - Si NO → genera la documentación final y para

---

## COSAS NUEVAS QUE DEBES CREAR (si no existen)

Busca en internet las mejores prácticas para cada una antes de implementar:

### Mejoras al Pipeline
- `pipeline/retry_manager.py` — sistema centralizado de reintentos con backoff
- `pipeline/clip_ranker.py` — rankea clips de Pexels por relevancia al guión usando Gemini
- `pipeline/voice_selector.py` — elige la voz óptima de ElevenLabs por canal y tono
- `pipeline/subtitle_styler.py` — subtítulos animados estilo TikTok con colores por canal

### Nuevas Automatizaciones
- `automation/trend_to_script.py` — de tendencia detectada a guión en < 5 minutos
- `automation/competitor_tracker.py` — analiza los 3 mejores competidores de cada nicho semanalmente
- `automation/seo_ab_tester.py` — genera 3 títulos por vídeo y registra cuál tiene mejor CTR
- `automation/affiliate_matcher.py` — detecta el producto afiliado más relevante por tema de vídeo

### Sistema de Monitorización
- `monitoring/health_checker.py` — verifica estado de todas las APIs cada hora
- `monitoring/revenue_tracker.py` — estima ingresos diarios de todos los canales
- `monitoring/alert_system.py` — envía email si algo falla o si un vídeo va viral

### Extensiones de Skills
Busca en `.copilot/skills/` y usa TODAS las capacidades disponibles:
- Si hay skill de marketing → aplícala al generador de descripciones
- Si hay skill de frontend → aplícala al dashboard
- Si hay skill de testing → genera tests para los módulos críticos
- Si hay skill de refactoring → pasa el código del pipeline por ella

---

## LO QUE NECESITO DE TI (SIEMPRE GRATUITO)

Cuando necesites algo que no está configurado, **pídelo con este formato
exacto** creando el archivo `NEEDS_FROM_HUMAN.md`:

```markdown
# Lo que necesito para continuar — [FECHA]

## ❌ Bloqueante (no puedo avanzar sin esto)
- [ ] **[NOMBRE_VARIABLE]** en el .env
  - Para qué lo necesito: [explicación específica]
  - Cómo conseguirlo GRATIS: [pasos exactos, URL, tiempo estimado]
  - Alternativa gratuita si no quieres esta: [alternativa]

## ⚠️ Mejora importante (puedo continuar sin esto, pero el sistema será mejor con ello)
- [ ] **[NOMBRE_VARIABLE]**
  - Para qué: [explicación]
  - Cómo: [pasos + URL]

## ✅ Lo que puedo hacer mientras tanto
- [lista de mejoras que SÍ puedo implementar sin esperar]
```

**Reglas para pedir recursos:**
- Solo pides APIs o servicios 100% gratuitos
- Siempre explicas exactamente para qué lo necesitas
- Siempre das el enlace directo donde conseguirlo
- Siempre das el tiempo estimado de setup
- Si existe una alternativa gratuita funcional, la implementas y no pides nada

---

## LIMPIEZA AUTOMÁTICA (ejecutar en cada iteración)

Antes de cada nueva iteración de mejora, limpia el proyecto:

```python
# Archivos que SIEMPRE son seguros eliminar:
SAFE_TO_DELETE = [
    "**/__pycache__/**",
    "**/*.pyc",
    "**/.DS_Store",
    "**/Thumbs.db",
    "outputs/temp_*",          # archivos temporales del pipeline
    "clips/temp_*",             # clips temporales
    "logs/master-*.log",        # logs de más de 7 días
]

# Archivos que revisar antes de eliminar (pide confirmación):
CHECK_BEFORE_DELETE = [
    # Scripts que no se importan en ningún otro archivo
    # Variables que no aparecen en .env.example
    # Carpetas vacías
]
```

**NUNCA elimines:**
- `.env` y `.env.example`
- `pipeline_queue.json`
- Cualquier archivo en `briefings/` o `research/`
- Archivos de `tests/`
- El `.github/` folder
- Cualquier AGENT.md o SKILL.md

---

## DOCUMENTO FINAL (genera cuando termines)

Cuando todos los criterios estén cumplidos, crea `FINAL_REPORT.md`:

```markdown
# VidFlow AI — Informe Final del Sistema
Generado automáticamente por los agentes de VidFlow AI
Fecha: [fecha]
Iteraciones completadas: [número]

## Resumen Ejecutivo
[2-3 párrafos explicando qué hace el sistema]

## Lo que se construyó
### Pipeline de Producción
[Explicación de cada módulo con su función]

### Sistema de Agentes
[Qué hace cada agente, cuándo corre, qué produce]

### Canales y Contenido
[Estado de cada canal, tipos de contenido, RPM estimado]

## Mejoras Implementadas Durante el Proceso
| Iteración | Problema | Solución | Archivo |
|---|---|---|---|
| 1 | Pantalla negra | Añadido downloader_footage.py | pipeline/downloader_footage.py |

## Cómo Usar el Sistema
### Para el usuario sin conocimientos técnicos
[Guía de 5 pasos, sin jerga técnica]

### Comandos del día a día
[Lista de comandos con su función en español]

## APIs y Servicios en Uso
| Servicio | Para qué | Gratuito | Límite |
|---|---|---|---|

## Proyección de Ingresos
[Tabla con estimación realista por mes y canal]

## Próximos Pasos Recomendados
[Lo que haría un humano para escalar el sistema más allá de la automatización]
```

---

## EMPIEZA AHORA

Lee primero `.github/copilot-instructions.md` para entender el contexto completo.
Luego ejecuta `python scripts/check_apis.py` para ver qué está disponible.
Luego empieza el bucle de mejora.

Reporta tu progreso creando `STATUS.md` al final de cada iteración:
```markdown
# Estado del Sistema — [FECHA] [HORA]
**Iteración actual**: #X
**Criterios completados**: X/10
**Trabajando en**: [descripción de la tarea actual]
**Próxima tarea**: [qué hará en la siguiente iteración]
**Bloqueantes**: [qué necesita del humano, si algo]
```

¡Empieza!
