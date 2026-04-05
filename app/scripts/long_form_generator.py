"""
Long-Form Video Generator: Compilación Automática de Clips
Combina top clips en un video largo (10-15 min) con intro/outro
"""

import os
import sys
import json
import subprocess
import asyncio
from typing import List, Dict, Any
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

FFMPEG_PATH = r"ffmpeg"
STORAGE_BASE = Path(r"app\storage")

async def reorder_clips_by_narrative(clips: List[Dict]) -> List[Dict]:
    """
    Usa Gemini para ordenar clips en secuencia narrativa coherente
    No solo por score, sino por flujo de historia
    
    Args:
        clips: Lista de clips con metadata
    
    Returns:
        Clips reordenados
    """
    print("🧠 Ordenando clips por narrativa con Gemini...")
    
    # Preparar resumen de clips para Gemini
    clips_summary = []
    for i, clip in enumerate(clips):
        clips_summary.append({
            'index': i,
            'category': clip.get('category', 'Otro'),
            'hook': clip.get('hook_description', '')[:100],
            'payoff': clip.get('payoff_description', '')[:100],
            'score': clip.get('virality_score', 0)
        })
    
    prompt = f"""Eres un editor de videos experto. Tienes {len(clips)} clips virales que debes ordenar para crear un video largo coherente.

CLIPS DISPONIBLES:
{json.dumps(clips_summary, indent=2)}

Tu tarea: reordenar estos clips para crear la MEJOR narrativa posible.

REGLAS:
1. Empezar con clip de alta energía (score alto)
2. Variar categorías para mantener interés
3. Crear arcos narrativos (tensión → release)
4. Terminar con un clip memorable (alto score)

DEVUELVE JSON:
{{
    "order": [2, 5, 1, 8, ...],  // Índices en el orden correcto
    "reasoning": "Por qué elegiste este orden"
}}
"""
    
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = await model.generate_content_async(prompt)
    
    try:
        text = response.text
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        
        data = json.loads(text.strip())
        order = data.get('order', list(range(len(clips))))
        
        print(f"✓ Orden narrativo calculado: {order}")
        print(f"  Reasoning: {data.get('reasoning', 'N/A')}")
        
        return [clips[i] for i in order if i < len(clips)]
        
    except Exception as e:
        print(f"⚠️ Error ordenando clips, usando order original: {e}")
        return clips

async def generate_intro_text(clips: List[Dict], project_title: str = "Compilación Viral") -> str:
    """
    Genera texto de intro usando Gemini
    """
    print("📝 Generando texto de intro...")
    
    categories = list(set(c.get('category', 'Viral') for c in clips))
    
    prompt = f"""Genera un texto de intro corto (15 segundos de lectura) para un video compilatorio.

TÍTULO: {project_title}
CATEGORÍAS: {', '.join(categories)}
CANTIDAD DE CLIPS: {len(clips)}

El texto debe:
- Crear expectativa
- Mencionar qué tipo de contenido verán
- Invitar a quedarse hasta el final

DEVUELVE SOLO EL TEXTO, máximo 2 líneas.
"""
    
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = await model.generate_content_async(prompt)
    
    intro_text = response.text.strip().replace('"', '')
    print(f"✓ Intro: {intro_text}")
    return intro_text

def create_text_video(text: str, output_path: str, duration: int = 5) -> str:
    """
    Crea un video simple con texto (intro/outro)
    """
    print(f"🎬 Creando video de texto: {output_path}")
    
    # Crear video con texto usando FFmpeg
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-f', 'lavfi',
        '-i', f'color=c=black:s=720x1280:d={duration}',
        '-vf', f"drawtext=text='{text}':fontsize=32:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2:fontfile='C\\:/Windows/Fonts/arial.ttf'",
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        output_path
    ]
    
    subprocess.run(cmd, check=True)
    return output_path

def create_transition(duration: float = 1.0) -> str:
    """
    Crea un video de transición (fade negro)
    """
    transition_path = STORAGE_BASE / 'temp' / 'transition.mp4'
    
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-f', 'lavfi',
        '-i', f'color=c=black:s=720x1280:d={duration}',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        str(transition_path)
    ]
    
    subprocess.run(cmd, check=True)
    return str(transition_path)

async def create_compilation_video(
    clips: List[Dict],
    output_path: str,
    project_title: str = "Compilación Viral"
) -> str:
    """
    Crea video largo a partir de clips
    
    Args:
        clips: Lista de clips (top 10-15)
        output_path: Dónde guardar el video final
        project_title: Título del proyecto
    
    Returns:
        Path del video compilado
    """
    print(f"\n{'='*60}")
    print(f"🎬 LONG-FORM VIDEO GENERATOR")
    print(f"{'='*60}\n")
    
    # 1. Ordenar clips por narrativa
    ordered_clips = await reorder_clips_by_narrative(clips[:15])  # Max 15 clips
    
    # 2. Generar intro
    intro_text = await generate_intro_text(ordered_clips, project_title)
    intro_path = STORAGE_BASE / 'temp' / 'intro.mp4'
    create_text_video(intro_text, str(intro_path), duration=5)
    
    # 3. Crear lista de concatenación
    concat_list = STORAGE_BASE / 'temp' / 'concat_list.txt'
    
    with open(concat_list, 'w') as f:
        # Intro
        f.write(f"file '{intro_path}'\n")
        
        # Transición
        transition_path = create_transition(1.0)
        
        # Clips con transiciones
        for clip in ordered_clips:
            clip_path = STORAGE_BASE / 'subtitled' / f"{clip['id']}.mp4"
            if not clip_path.exists():
                clip_path = STORAGE_BASE / 'clips' / f"{clip['id']}.mp4"
            
            if clip_path.exists():
                f.write(f"file '{clip_path}'\n")
                f.write(f"file '{transition_path}'\n")
        
        # Outro
        outro_text = "¡Gracias por ver! Suscríbete para más contenido viral"
        outro_path = STORAGE_BASE / 'temp' / 'outro.mp4'
        create_text_video(outro_text, str(outro_path), duration=3)
        f.write(f"file '{outro_path}'\n")
    
    # 4. Concatenar todo
    print("🔧 Concatenando clips...")
    
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_list),
        '-c', 'copy',
        output_path
    ]
    
    subprocess.run(cmd, check=True)
    
    print(f"\n✅ VIDEO LARGO COMPLETADO: {output_path}")
    print(f"   Duración: ~{len(ordered_clips) * 45} segundos")
    print(f"   Clips incluidos: {len(ordered_clips)}\n")
    
    return output_path

# CLI
if __name__ == "__main__":
    import asyncio
    
    # Test con clips de ejemplo
    test_clips = [
        {
            'id': 'clip1',
            'category': 'Humor',
            'hook_description': 'Reacción inesperada',
            'payoff_description': 'Final sorprendente',
            'virality_score': 95
        },
        {
            'id': 'clip2',
            'category': 'Educativo',
            'hook_description': 'Dato impactante',
            'payoff_description': 'Explicación clara',
            'virality_score': 88
        }
    ]
    
    output = "test_compilation.mp4"
    
    asyncio.run(create_compilation_video(test_clips, output))
