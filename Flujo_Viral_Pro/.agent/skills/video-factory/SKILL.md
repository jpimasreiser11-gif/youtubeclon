---
name: video-factory
description: Habilidad para orquestar la producción de video.
---
# Fábrica de Video

## Objetivo
Sintetizar el archivo MP4 final a partir de un guion y recursos visuales.

## Instrucciones
1. Recibe el texto del guion y el ID del video.
2. Ejecuta python scripts/tts.py --text '...' --output temp/audio.mp3 para generar el audio.
3. Ejecuta python scripts/fetch_video.py --keywords '...' --output temp/video_stock.mp4 para obtener visuales.
4. Ejecuta python scripts/render.py --audio temp/audio.mp3 --video temp/video_stock.mp4 --output final_video.mp4 para ensamblar, editar y añadir subtítulos.
5. Verifica que el archivo final exista y sea reproducible.
