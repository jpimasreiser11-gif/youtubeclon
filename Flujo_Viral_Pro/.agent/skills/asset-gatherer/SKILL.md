name: asset-gatherer
description: Genera audio TTS neural y descarga videos de stock correspondientes al guion.

# Asset Gatherer Skill

## Cuándo usar
Úsalo cuando un video esté en estado 'scripted' o se solicite explícitamente "preparar activos".

## Flujo de Ejecución

### 1. Síntesis de Audio (Edge-TTS)
- **Herramienta**: Librería `edge-tts` (Python).
- **Selección de Voz**:
  - Para contenido en Español: `es-MX-DaliaNeural` (Femenina, clara) o `es-AR-TomasNeural` (Masculino, enérgico).
  - Para contenido en Inglés: `en-US-ChristopherNeural` (Serio) o `en-US-GuyNeural` (Casual).
- **Acción**: Genera un archivo `.mp3` único en `assets/audio/{id}.mp3` combinando Hook + Body + CTA.
- **Validación**: Verifica que el archivo de audio se haya creado y tenga un tamaño > 0 bytes.

### 2. Adquisición Visual (Pexels API)
- **Herramienta**: `requests` a Pexels API.
- **Lógica**: Lee las `visual_keywords` del JSON del guion en la DB.
- **Consulta**: `https://api.pexels.com/videos/search?query={keyword}&per_page=3&orientation=portrait&size=medium`.
- **Restricciones**:
  - Descarga 3-5 clips por video.
  - Almacena en `assets/video_clips/{id}/`.
  - Implementa un **Mecanismo de Caché**: Antes de descargar, verifica si ya existe un clip para esa keyword en una carpeta común `assets/video_clips/common/` para ahorrar cuota de API.

### 3. Actualización de Estado
- Si ambos pasos son exitosos, actualiza el registro en la DB a estado 'assets_ready'.
