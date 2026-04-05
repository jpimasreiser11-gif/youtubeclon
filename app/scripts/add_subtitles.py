import os
import sys
import subprocess
import argparse
from faster_whisper import WhisperModel

def add_subtitles_to_clip(clip_id, style='tiktok', font='Montserrat Bold', size=24, color='#FFFF00', position='center'):
    """
    Añade subtítulos a un clip usando Whisper + FFmpeg
    
    Args:
        clip_id: ID del clip
        style: Estilo de subtítulos ('tiktok', 'youtube', 'minimal')
        font: Fuente a utilizar
        size: Tamaño de fuente
        color: Color en formato hex
        position: Posición ('top', 'center', 'bottom')
    """
    
    STORAGE_BASE = r"c:\\Users\\jpima\\Downloads\\edumind---ai-learning-guide\\app\\storage"
    FFMPEG_PATH = r"C:\\Users\\jpima\\Downloads\\edumind---ai-learning-guide\\data\\ffmpeg.exe"
    
    video_path = os.path.join(STORAGE_BASE, "previews", f"{clip_id}.mp4")
    output_path = os.path.join(STORAGE_BASE, "previews", f"{clip_id}_subtitled.mp4")
    
    if not os.path.exists(video_path):
        print(f"Error: Video not found at {video_path}")
        return None
    
    print(f"Adding subtitles to clip {clip_id}...")
    
    # 1. Transcribir con Whisper (word-level timestamps)
    print("Transcribing with Whisper...")
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(video_path, word_timestamps=True)
    
    # 2. Crear archivo .ass con estilos
    ass_file = os.path.join(STORAGE_BASE, "temp", f"{clip_id}.ass")
    os.makedirs(os.path.dirname(ass_file), exist_ok=True)
    
    print(f"Generating .ass file with style: {style}")
    generate_ass_file(segments, ass_file, style, font, size, color, position)
    
    # 3. Quemar subtítulos con FFmpeg
    print("Burning subtitles into video...")
    subprocess.run([
        FFMPEG_PATH, '-y',
        '-i', video_path,
        '-vf', f"ass={ass_file}",
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'copy',
        output_path
    ], check=True)
    
    print(f"✓ Subtitled video saved: {output_path}")
    return output_path

def generate_ass_file(segments, output_file, style, font, size, color, position):
    """
    Genera un archivo .ass (Advanced SubStation Alpha) con estilos personalizados
    """
    
    # Convertir color hex a formato ASS (BGR)
    ass_color = convert_color_to_ass(color)
    
    # Determinar alineación según posición
    alignment = {
        'top': '8',      # Top center
        'center': '5',   # Middle center
        'bottom': '2'    # Bottom center
    }[position]
    
    # Estilo outline según preset
    outline = '3' if style == 'tiktok' else '2'
    
    # Header del archivo ASS
    ass_content = f"""[Script Info]
Title: Auto-generated Subtitles
ScriptType: v4.00+
PlayDepth: 0

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,{font},{size},{ass_color},&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{outline},1,{alignment},10,10,10,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    
    # Añadir cada segmento
    for segment in segments:
        for word in segment.words:
            start_time = format_ass_time(word.start)
            end_time = format_ass_time(word.end)
            text = word.word.strip()
            
            if text:
                # Si es estilo TikTok, aplicar efecto de resaltado palabra por palabra
                if style == 'tiktok':
                    text = f"{{\\b1}}{text}{{\\b0}}"
                
                ass_content += f"Dialogue: 0,{start_time},{end_time},Default,,0,0,0,,{text}\n"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(ass_content)
    
    print(f"✓ ASS file generated: {output_file}")

def convert_color_to_ass(hex_color):
    """Convierte color hex (#RRGGBB) a formato ASS (&HAABBGGRR)"""
    hex_color = hex_color.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"&H00{b:02X}{g:02X}{r:02X}"

def format_ass_time(seconds):
    """Convierte segundos a formato ASS (H:MM:SS.CS)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centisecs = int((seconds - int(seconds)) * 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add subtitles to video clips")
    parser.add_argument("--clip-id", required=True, help="Clip ID")
    parser.add_argument("--style", default="tiktok", choices=["tiktok", "youtube", "minimal"])
    parser.add_argument("--font", default="Montserrat Bold")
    parser.add_argument("--size", type=int, default=24)
    parser.add_argument("--color", default="#FFFF00")
    parser.add_argument("--position", default="center", choices=["top", "center", "bottom"])
    
    args = parser.parse_args()
    
    add_subtitles_to_clip(
        args.clip_id,
        args.style,
        args.font,
        args.size,
        args.color,
        args.position
    )
