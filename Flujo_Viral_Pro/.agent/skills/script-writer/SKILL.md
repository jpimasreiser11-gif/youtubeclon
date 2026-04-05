name: script-writer
description: Genera guiones para videos de formato corto (TikTok/Shorts) optimizados para alta retención y viralidad.

# Script Writer Skill

## Cuándo usar
Utiliza esta habilidad cuando el usuario solicite "generar ideas", "escribir guiones" o "planificar contenido" para un nicho específico.

## Instrucciones del Modelo (Gemini)
1. **Análisis de Nicho**: Identifica subtemas de alto compromiso dentro del nicho solicitado (ej. Curiosidades Históricas, Trucos Tech, Motivación Estoica).
2. **Estructura Obligatoria**: El guion DEBE seguir esta estructura de 3 actos para maximizar la retención:
   - **Hook (Gancho) [0-3s]**: Una afirmación impactante, pregunta retórica o paradoja visual.
   - **Body (Cuerpo) [3-50s]**: Entrega rápida de información. Frases cortas. Ritmo acelerado.
   - **CTA (Llamada a la acción) [50-60s]**: Instrucción clara (ej. "Suscríbete para más").

## Formato de Salida
Retorna SIEMPRE un objeto JSON válido, no texto plano conversacional.

```json
{
  "title": "Título Viral",
  "niche": "Nicho Seleccionado",
  "hook": "Texto del gancho...",
  "body": "Texto del cuerpo...",
  "cta": "Texto del CTA...",
  "visual_keywords": ["palabra_clave1", "palabra_clave2", "palabra_clave3"],
  "suggested_bg_music_mood": "Energetic/Sad/Suspense"
}
```

## Persistencia
Inmediatamente después de generar, utiliza `src/utils/db_manager.py` (que crearás) para insertar el registro en la base de datos con estado 'scripted'.

## Dependencias
- Requiere acceso a `src/utils/db_init.py` para conocer el esquema.
- Utiliza la API de Gemini configurada en el entorno.
