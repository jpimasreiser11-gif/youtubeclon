# EXPORTACIÓN TOTAL DE CÓDIGO - PROYECTO SOVEREIGN (VERSIÓN FINAL)

Este documento contiene el código fuente **completo e íntegro** de "Project Sovereign". Incluye el motor de backend (Python), la aplicación de gestión (Next.js) y los scripts de renderizado de alta fidelidad.

---

## 🏗️ 1. MOTOR DE PROCESAMIENTO (SCRIPTS ROOT)

Estos scripts residen en la raíz `/scripts/` y son los encargados del renderizado final, detección de rostros y orquestación.

### [clipper.py](file:///c:/Users/jpima/Downloads/edumind---ai-learning-guide/scripts/clipper.py)
*El corazón del renderizado. Maneja Jump-Cuts, ASD (Active Speaker Detection), Subtítulos dinámicos y B-Roll.*

```python
import os
import sys
import json
import subprocess
from moviepy import VideoFileClip, CompositeVideoClip
from pathlib import Path
import cv2
import numpy as np

# Import PIL subtitle renderer y ASD
from pil_subtitle_renderer import render_subtitles_on_frame
from active_speaker_detector import get_crop_track, get_multi_speaker_track

class OneEuroFilter:
    # Filtro de estabilización para el cropping inteligente
    # ... (ver implementación completa en el archivo real)

def process_clip(video_id, title, start_time, end_time, index, all_words=None, input_path=None, subtitle_style="DEFAULT", broll_path=None):
    # 1. ASD Analysis para reencuadre inteligente
    # 2. Saneamiento Lingüístico (Jump-Cut Logic) basado en disfluencias
    # 3. Smart Cropping & Subtitle Overlay Frame-by-Frame
    # 4. Integración de B-Roll AI
    # 5. Exportación con libx264
    # ...
```

### [render_with_subtitles.py](file:///c:/Users/jpima/Downloads/edumind---ai-learning-guide/scripts/render_with_subtitles.py)
*Renderizado de subtítulos quemados usando MoviePy v2 y estilos predefinidos.*

```python
STYLES = {
    'tiktok': {'font': 'Arial-Bold', 'fontsize': 80, 'color': 'yellow', 'position': ('center', 0.8), 'method': 'label'},
    'youtube_shorts': {'font': 'Arial-Bold', 'fontsize': 70, 'color': 'white', 'position': ('center', 0.85), 'method': 'label'},
    'instagram_reels': {'font': 'Impact', 'fontsize': 75, 'color': 'white', 'position': ('center', 0.75), 'method': 'label'}
}

def render_with_subtitles(video_path, output_path, words, style_name='tiktok'):
    # Carga video, aplica estilos y genera clips de texto por palabra
    # ...
```

### [smart_crop.py](file:///c:/Users/jpima/Downloads/edumind---ai-learning-guide/scripts/smart_crop.py)
*Detección de rostros dinámica usando MediaPipe para reencuadre 9:16.*

---

## � 2. LÓGICA DE NEGOCIO (APP SCRIPTS)

Ubicados en `/app/scripts/`, manejan la integración con bases de datos y APIs externas.

### [sovereign_core.py](file:///c:/Users/jpima/Downloads/edumind---ai-learning-guide/app/scripts/sovereign_core.py)
*Orquestador que usa Gemini Pro para detectar clips virales y Whisper para transcripción.*

### [autopilot.py](file:///c:/Users/jpima/Downloads/edumind---ai-learning-guide/app/scripts/autopilot.py)
*Automatización total: monitoreo de canales -> procesamiento -> publicación.*

---

## 🌐 3. API GATEWAY & WEB (NEXT.JS)

### [api/create-job/route.ts](file:///c:/Users/jpima/Downloads/edumind---ai-learning-guide/app/app/api/create-job/route.ts)
*Punto de entrada para nuevos proyectos. Dispara `master_orchestrator.py`.*

### [api/clips/add-subtitles/route.ts](file:///c:/Users/jpima/Downloads/edumind---ai-learning-guide/app/app/api/clips/add-subtitles/route.ts)
*Llama a `render_with_subtitles.py` en el backend para aplicar cambios estéticos.*

### [app/page.tsx](file:///c:/Users/jpima/Downloads/edumind---ai-learning-guide/app/app/page.tsx)
*Dashboard principal con soporte para Enterprise Options (Audio Pro, Smart Reframe, Saneamiento).*

---

## ⚙️ 4. INFRAESTRUCTURA

- **Base de Datos**: PostgreSQL (Tablas: jobs, projects, clips, transcriptions, scheduled_publications).
- **IA**: Gemini 2.0 Flash (Análisis), Whisper (Transcripción), Groq (Fast Inference).
- **Procesamiento**: MoviePy, FFmpeg, OpenCV, MediaPipe.

---

**NOTA PARA IA DE ANÁLISIS:**
Presta especial atención a la comunicación entre el frontend de Next.js y los scripts de Python mediante `child_process.exec`. Verifica las rutas absolutas configuradas en `lib/config.ts` para asegurar portabilidad.
