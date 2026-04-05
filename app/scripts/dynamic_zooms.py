"""
Dynamic Zooms: Añade Zooms Automáticos en Momentos Clave
Zoom-in en hook (crear tensión)
Zoom-out en payoff (release)
"""

import subprocess
from typing import Dict, Any
from pathlib import Path

FFMPEG_PATH = r"ffmpeg"

def generate_zoom_filter(
    hook_time: float,
    payoff_time: float,
    duration: float,
    hook_zoom: float = 1.1,
    payoff_zoom: float = 0.95
) -> str:
    """
    Genera filtro FFmpeg para zooms dinámicos
    
    Args:
        hook_time: Momento del hook en segundos
        payoff_time: Momento del payoff en segundos
        duration: Duración total del clip
        hook_zoom: Factor de zoom en hook (default: 1.1 = 110%)
        payoff_zoom: Factor de zoom en payoff (default: 0.95 = 95%)
    
    Returns:
        String del filtro zoompan
    """
    hook_duration = 2.0  # Duración del zoom-in en hook
    payoff_duration = 1.5  # Duración del zoom-out en payoff
    
    # Expresión zoompan
    # z = zoom level (1.0 = normal)
    # t = tiempo actual en segundos
    
    zoom_expr = f"""
    zoompan=z='
    if(between(t,{hook_time},{hook_time + hook_duration}),
        {hook_zoom},
        if(between(t,{payoff_time},{payoff_time + payoff_duration}),
            {payoff_zoom},
            1.0
        )
    )':d=1:s=720x1280
    """.strip().replace('\n', '').replace('  ', '')
    
    return zoom_expr

def add_dynamic_zooms(
    input_video: str,
    output_video: str,
    clip_metadata: Dict[str, Any]
) -> str:
    """
    Añade zooms dinámicos basados en metadata del clip
    
    Args:
        input_video: Video de entrada
        output_video: Video de salida
        clip_metadata: Metadata con hook/payoff info
            {
                "start_time": 10.0,
                "end_time": 55.0,
                "hook_description": "...",
                "payoff_description": "..."
            }
    
    Returns:
        Path del video procesado
    """
    print(f"🎯 Añadiendo zooms dinámicos...")
    
    # Calcular tiempos relativos (desde el inicio del clip)
    clip_start = clip_metadata.get('start_time', 0)
    clip_end = clip_metadata.get('end_time', 60)
    duration = clip_end - clip_start
    
    # Hook suele estar al inicio (primeros 5 segundos)
    hook_time = 2.0  # 2 segundos desde el inicio del clip
    
    # Payoff suele estar cerca del final
    payoff_time = duration - 5.0  # 5 segundos antes del final
    
    # Generar filtro
    zoom_filter = generate_zoom_filter(hook_time, payoff_time, duration)
    
    # Aplicar con FFmpeg
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', input_video,
        '-vf', zoom_filter,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'copy',
        output_video
    ]
    
    subprocess.run(cmd, check=True)
    
    print(f"✓ Zooms aplicados: {output_video}")
    return output_video

def add_zoom_on_score(
    input_video: str,
    output_video: str,
    virality_score: int
) -> str:
    """
    Añade zoom más agresivo si el score es muy alto
    
    Args:
        virality_score: Score de viralidad (0-100)
    """
    # Ajustar intensidad del zoom según score
    if virality_score >= 90:
        hook_zoom = 1.15  # Zoom más agresivo
        payoff_zoom = 0.92
    elif virality_score >= 80:
        hook_zoom = 1.1
        payoff_zoom = 0.95
    else:
        hook_zoom = 1.05  # Zoom sutil
        payoff_zoom = 0.97
    
    zoom_expr = f"zoompan=z='if(lt(t,3),{hook_zoom},1.0)':d=1:s=720x1280"
    
    cmd = [
        FFMPEG_PATH,
        '-y',
        '-i', input_video,
        '-vf', zoom_expr,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'copy',
        output_video
    ]
    
    subprocess.run(cmd, check=True)
    return output_video

# CLI
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 3:
        print("Usage: python dynamic_zooms.py <input> <output> <metadata_json>")
        sys.exit(1)
    
    input_vid = sys.argv[1]
    output_vid = sys.argv[2]
    metadata = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    
    add_dynamic_zooms(input_vid, output_vid, metadata)
