name: video-editor
description: Compila audio, video y subtítulos sincronizados (Karaoke) en un MP4 final usando MoviePy y WhisperX.

# Video Editor Skill

## Cuándo usar
Cuando el estado del video es 'assets_ready' y se requiere renderizar el producto final.

## Especificaciones Técnicas de Implementación
Debes crear/ejecutar `src/media_engine/render_core.py` siguiendo esta lógica estricta:

### 1. Alineación Forzada (WhisperX)
- **Problema**: Los timestamps normales de Whisper no son precisos para efectos de palabras rápidas.
- **Solución**: Usa whisperx.
  - Transcribe el audio: `model = whisperx.load_model("small", device="cpu", compute_type="int8")`.
  - Carga el modelo de alineación: `whisperx.load_align_model(...)`.
  - Ejecuta `whisperx.align(...)` para obtener `word_segments`.
- **Salida**: Una lista de diccionarios con `{word, start, end}` precisos.

### 2. Composición Visual (MoviePy)
- **Carga de Clips**: Importa los videos descargados.
- **Transformación**:
  - Redimensiona a 1080x1920 (9:16) usando `moviepy.video.fx.all.resize`.
  - Aplica crop central para llenar la pantalla sin bordes negros.
  - Haz un bucle (loop) o concatena los clips para igualar la duración del audio.
- **Audio**: Establece el audio del video compuesto usando el MP3 de TTS.

### 3. Generación de Subtítulos "Karaoke"
- Itera sobre los `word_segments` de WhisperX.
- Para cada palabra (o par de palabras), crea un `TextClip`.
- **Estilo Viral**:
  - Fuente: "Impact" o "Arial-Bold".
  - Color: Blanco con borde Negro (Stroke=2) y sombra ligera.
  - Efecto de Resaltado: La palabra actual debe ser de color Amarillo o Verde brillante, o ligeramente más grande (zoom 1.1x).
- **Posición**: Centro de la pantalla o tercio inferior.
- **Optimización**: Usa `CompositeVideoClip` con cuidado. Cierra todos los clips explícitamente (`.close()`) al final para evitar fugas de memoria (Memory Leaks) comunes en MoviePy.

### 4. Renderizado
- **Salida**: `assets/final_renders/video_{id}.mp4`.
- **Parámetros**: `fps=24, codec='libx264', audio_codec='aac', preset='ultrafast'` (para pruebas) o `medium` (producción).
- **Actualiza DB** a 'rendered'.
