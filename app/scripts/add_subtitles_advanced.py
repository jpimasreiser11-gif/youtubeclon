"""
Advanced Subtitle Generation with Word-by-Word Karaoke Timing
Genera subtítulos animados estilo viral con:
- Timing palabra por palabra (karaoke style)
- IA detecta palabras a resaltar
- Presets por plataforma (TikTok, Shorts, Reels)
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from faster_whisper import WhisperModel
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

FFMPEG_PATH = r"ffmpeg"

# Presets por plataforma
SUBTITLE_PRESETS = {
    'tiktok': {
        'name': 'TikTok Viral',
        'font': 'Montserrat Black',
        'size': 24,
        'primary_color': '&H00FFFF',  # Amarillo brillante
        'outline_color': '&H000000',  # Negro
        'outline': 3,
        'bold': True,
        'position_y': 80,  # % desde arriba
        'bounce': True,  # Animación bounce
        'alignment': 5,  # Centro
    },
    'shorts': {
        'name': 'YouTube Shorts',
        'font': 'Arial Bold',
        'size': 20,
        'primary_color': '&HFFFFFF',  # Blanco
        'outline_color': '&H000000',
        'outline': 2,
        'bold': True,
        'position_y': 85,
        'bounce': False,
        'alignment': 2,  # Centro abajo
    },
    'reels': {
        'name': 'Instagram Reels',
        'font': 'Helvetica Neue',
        'size': 18,
        'primary_color': '&HE0E0E0',  # Gris claro
        'outline_color': '&H000000',
        'outline': 1,
        'bold': False,
        'position_y': 88,
        'bounce': False,
        'alignment': 2,
    },
    'standard': {
        'name': 'Standard',
        'font': 'Arial',
        'size': 16,
        'primary_color': '&HFFFFFF',
        'outline_color': '&H000000',
        'outline': 2,
        'bold': True,
        'position_y': 90,
        'bounce': False,
        'alignment': 2,
    }
}

class WordTimestamp:
    """Representa una palabra con timestamps"""
    def __init__(self, text: str, start: float, end: float):
        self.text = text.strip()
        self.start = start
        self.end = end
        self.duration = end - start
        self.is_highlight = False
    
    def __repr__(self):
        return f"Word({self.text}, {self.start:.2f}-{self.end:.2f})"

def transcribe_with_word_timestamps(audio_path: str) -> List[WordTimestamp]:
    """
    Transcribe audio y extrae timestamps palabra por palabra usando Whisper
    """
    print("🎙️ Transcribiendo con Whisper (word-level timestamps)...")
    
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_path, beam_size=5, word_timestamps=True)
    
    words = []
    for segment in segments:
        if hasattr(segment, 'words'):
            for word in segment.words:
                words.append(WordTimestamp(
                    text=word.word.strip(),
                    start=word.start,
                    end=word.end
                ))
    
    print(f"✓ {len(words)} palabras transcritas")
    return words

async def detect_highlight_words(words: List[WordTimestamp], context: str = "") -> List[str]:
    """
    Usa Gemini para detectar qué palabras tienen mayor impacto emocional/viral
    
    Args:
        words: Lista de palabras con timestamps
        context: Descripción del clip (hook/payoff) para mejor análisis
    
    Returns:
        Lista de palabras a resaltar
    """
    print("🧠 Analizando palabras clave con Gemini...")
    
    # Preparar texto para análisis
    transcript_text = " ".join([w.text for w in words])
    
    prompt = f"""Analiza este fragmento de un video viral y marca las 5-10 palabras con MAYOR impacto emocional o viral.

Transcript:
{transcript_text}

Contexto del clip:
{context}

Devuelve SOLO un JSON con este formato:
{{
    "highlight_words": ["PALABRA1", "PALABRA2", "PALABRA3"]
}}

Reglas:
- Palabras que generan emoción fuerte (sorpresa, shock, risa)
- Palabras clave del mensaje principal
- Números importantes
- Exclamaciones
- NO artículos ni conectores
"""
    
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = await model.generate_content_async(prompt)
    
    try:
        # Extraer JSON de la respuesta
        text = response.text
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        
        data = json.loads(text.strip())
        highlight_words = [w.upper() for w in data.get('highlight_words', [])]
        
        print(f"✓ {len(highlight_words)} palabras marcadas para highlight")
        return highlight_words
        
    except Exception as e:
        print(f"⚠️ Error al parsear respuesta de Gemini: {e}")
        return []

def mark_highlights(words: List[WordTimestamp], highlight_words: List[str]) -> List[WordTimestamp]:
    """
    Marca palabras que deben ser resaltadas
    """
    for word in words:
        if word.text.upper() in highlight_words:
            word.is_highlight = True
    
    highlighted_count = sum(1 for w in words if w.is_highlight)
    print(f"✓ {highlighted_count} palabras marcadas para animación especial")
    
    return words

def generate_ass_subtitles(
    words: List[WordTimestamp],
    output_path: str,
    preset: str = 'tiktok'
) -> str:
    """
    Genera archivo .ass con subtítulos karaoke estilo viral
    
    Args:
        words: Lista de palabras con timestamps
        output_path: Ruta donde guardar el archivo .ass
        preset: Preset de estilo (tiktok, shorts, reels, standard)
    
    Returns:
        Ruta del archivo .ass generado
    """
    print(f"📝 Generando subtítulos {preset}...")
    
    style = SUBTITLE_PRESETS.get(preset, SUBTITLE_PRESETS['standard'])
    
    # Header ASS
    ass_content = f"""[Script Info]
Title: Viral Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style['font']},{style['size']},{style['primary_color']},&H000000FF,{style['outline_color']},&H00000000,{'-1' if style['bold'] else '0'},0,0,0,100,100,0,0,1,{style['outline']},0,{style['alignment']},10,10,{style['position_y']},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    # Agrupar palabras en líneas (máximo 3 palabras por línea para mejor legibilidad)
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        
        # Nueva línea cada 3 palabras o si hay pausa larga
        if len(current_line) >= 3:
            lines.append(current_line)
            current_line = []
    
    if current_line:  # Añadir última línea
        lines.append(current_line)
    
    # Generar eventos ASS con karaoke timing
    for line_words in lines:
        start_time = line_words[0].start
        end_time = line_words[-1].end
        
        # Construir texto con karaoke timing \k
        karaoke_text = ""
        for word in line_words:
            # Duración en centésimas de segundo
            duration_cs = int((word.end - word.start) * 100)
            
            # Aplicar efectos según si es highlight
            if word.is_highlight:
                # Highlight: amarillo brillante + scale up
                word_text = f"{{\\k{duration_cs}\\c&H00FFFF&\\t(0,200,\\fscx120\\fscy120)\\t(200,400,\\fscx100\\fscy100)}}{word.text.upper()}"
            else:
                # Normal: color del preset
                word_text = f"{{\\k{duration_cs}}}{word.text}"
            
            karaoke_text += word_text + " "
        
        # Bounce effect para TikTok
        if style['bounce']:
            karaoke_text = "{\\move(0,0,0,-10,0,100)\\move(0,-10,0,0,100,200)}" + karaoke_text
        
        # Formato de timestamp ASS: H:MM:SS.CC
        start_ass = format_ass_time(start_time)
        end_ass = format_ass_time(end_time)
        
        ass_content += f"Dialogue: 0,{start_ass},{end_ass},Default,,0,0,0,,{karaoke_text.strip()}\n"
    
    # Guardar archivo
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    print(f"✓ Archivo .ass generado: {output_path}")
    return output_path

def format_ass_time(seconds: float) -> str:
    """Convierte segundos a formato ASS (H:MM:SS.CC)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds % 1) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"

def burn_subtitles_to_video(
    video_input: str,
    subtitle_file: str,
    video_output: str
) -> str:
    """
    Burn-in de subtítulos al video usando FFmpeg
    """
    print("🔥 Aplicando subtítulos al video...")
    
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', video_input,
        '-vf', f"ass={subtitle_file}",
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'copy',
        video_output
    ]
    
    subprocess.run(cmd, check=True)
    
    print(f"✓ Video con subtítulos generado: {video_output}")
    return video_output

async def add_advanced_subtitles(
    video_path: str,
    audio_path: str,
    output_path: str,
    preset: str = 'tiktok',
    context: str = ""
) -> str:
    """
    Pipeline completo de subtítulos avanzados
    
    Args:
        video_path: Video de entrada
        audio_path: Audio del video (para Whisper)
        output_path: Video de salida con subtítulos
        preset: Estilo de subtítulos (tiktok, shorts, reels)
        context: Contexto del clip para análisis de IA
    
    Returns:
        Ruta del video con subtítulos
    """
    print(f"\n🎬 Generando subtítulos avanzados ({preset})...\n")
    
    # 1. Transcribir con Whisper (word-level)
    words = transcribe_with_word_timestamps(audio_path)
    
    # 2. IA detecta palabras clave
    highlight_words = await detect_highlight_words(words, context)
    
    # 3. Marcar highlights
    words = mark_highlights(words, highlight_words)
    
    # 4. Generar archivo .ass
    subtitle_file = output_path.replace('.mp4', '.ass')
    generate_ass_subtitles(words, subtitle_file, preset)
    
    # 5. Burn-in al video
    output_video = burn_subtitles_to_video(video_path, subtitle_file, output_path)
    
    print("\n✅ Subtítulos avanzados completados!\n")
    return output_video

# CLI para testing
if __name__ == "__main__":
    import asyncio
    
    if len(sys.argv) < 4:
        print("Usage: python add_subtitles_advanced.py <video> <audio> <output> [preset]")
        print("Presets: tiktok, shorts, reels, standard")
        sys.exit(1)
    
    video = sys.argv[1]
    audio = sys.argv[2]
    output = sys.argv[3]
    preset = sys.argv[4] if len(sys.argv) > 4 else 'tiktok'
    
    asyncio.run(add_advanced_subtitles(video, audio, output, preset))
