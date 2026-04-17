# FEATURES

## Pipeline
- Trend discovery multi-fuente (Google Trends, YouTube, Reddit, News)
- Script generation por canal con tono/nicho específico
- TTS escalonado con fallback (`ElevenLabs -> Edge -> gTTS`)
- Video build con B-roll, subtítulos y encode final
- Metadata SEO y estado persistente en DB

## Operación
- Orquestación por canal y ejecución paralela diaria
- Logs de pipeline en tiempo real
- Scheduler para publicaciones diferidas
- Dashboard con KPIs y actividad reciente

## Calidad y escalabilidad
- Humanizer integrado en script + metadata
- Quota manager central (soft-limit) para APIs
- Fallback chains explícitas para servicios externos
- Skills personalizadas por canal y por dominio técnico

## Visual y marca
- Design system master + variantes por canal
- Assets brand organizados y prompts Banana reutilizables
- Intro Remotion opcional por canal integrada al build de video

