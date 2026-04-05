"""
Auto-Reframe: Crop Dinámico Siguiendo la Cara
Usa MediaPipe para detectar caras y mantenerlas centradas en el frame
Ideal para convertir videos horizontales en verticales (9:16)
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import List, Tuple, Dict
import subprocess
import json
from pathlib import Path

mp_face_detection = mp.solutions.face_detection

class FaceKeyframe:
    """Representa la posición de una cara en un frame específico"""
    def __init__(self, time: float, center_x: float, center_y: float, width: float, height: float):
        self.time = time
        self.center_x = center_x  # 0-1 (normalized)
        self.center_y = center_y  # 0-1
        self.width = width
        self.height = height

def detect_face_keyframes(video_path: str, sample_rate: int = 10) -> List[FaceKeyframe]:
    """
    Detecta caras en el video y genera keyframes de posición
    
    Args:
        video_path: Path al video
        sample_rate: Analizar 1 de cada N frames (default: 10)
    
    Returns:
        Lista de keyframes con posición de cara
    """
    print(f"🔍 Detectando caras en {video_path}...")
    
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    keyframes = []
    frame_idx = 0
    
    with mp_face_detection.FaceDetection(
        model_selection=1,  # 1 = full range, 0 = short range
        min_detection_confidence=0.5
    ) as face_detection:
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Analizar solo cada N frames
            if frame_idx % sample_rate == 0:
                # Convertir a RGB (MediaPipe requiere RGB)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_detection.process(rgb_frame)
                
                if results.detections:
                    # Tomar la primera cara detectada
                    detection = results.detections[0]
                    bbox = detection.location_data.relative_bounding_box
                    
                    center_x = bbox.xmin + bbox.width / 2
                    center_y = bbox.ymin + bbox.height / 2
                    
                    time = frame_idx / fps
                    
                    keyframes.append(FaceKeyframe(
                        time=time,
                        center_x=center_x,
                        center_y=center_y,
                        width=bbox.width,
                        height=bbox.height
                    ))
                    
                    if len(keyframes) % 10 == 0:
                        print(f"  Procesado {frame_idx}/{total_frames} frames ({len(keyframes)} caras detectadas)")
            
            frame_idx += 1
    
    cap.release()
    
    print(f"✓ {len(keyframes)} keyframes de cara detectados")
    return keyframes

def smooth_keyframes(keyframes: List[FaceKeyframe], window_size: int = 5) -> List[FaceKeyframe]:
    """
    Suaviza los keyframes para evitar movimientos bruscos
    Usa promedio móvil
    """
    if len(keyframes) < window_size:
        return keyframes
    
    smoothed = []
    
    for i, kf in enumerate(keyframes):
        # Tomar ventana de keyframes alrededor del actual
        start = max(0, i - window_size // 2)
        end = min(len(keyframes), i + window_size // 2 + 1)
        window = keyframes[start:end]
        
        # Calcular promedio
        avg_x = sum(k.center_x for k in window) / len(window)
        avg_y = sum(k.center_y for k in window) / len(window)
        
        smoothed.append(FaceKeyframe(
            time=kf.time,
            center_x=avg_x,
            center_y=avg_y,
            width=kf.width,
            height=kf.height
        ))
    
    return smoothed

def generate_crop_filter(keyframes: List[FaceKeyframe], target_width: int = 720, target_height: int = 1280) -> str:
    """
    Genera filtro FFmpeg para crop dinámico
    
    Args:
        keyframes: Lista de posiciones de cara
        target_width: Ancho objetivo (default: 720 para 9:16)
        target_height: Alto objetivo (default: 1280 para 9:16)
    
    Returns:
        String del filtro FFmpeg
    """
    if not keyframes:
        # Fallback: crop centrado estático
        return f"crop={target_width}:{target_height}"
    
    # Generar expresiones para x e y que cambian con el tiempo
    # FFmpeg permite expresiones basadas en tiempo usando 't'
    
    # Crear interpolación lineal entre keyframes
    x_expr = "iw/2-w/2"  # Default: centro
    y_expr = "ih/2-h/2"
    
    if len(keyframes) > 1:
        # Construir expresión complex con 'if' statements basados en tiempo
        x_conditions = []
        y_conditions = []
        
        for i, kf in enumerate(keyframes):
            if i < len(keyframes) - 1:
                next_kf = keyframes[i + 1]
                
                # Calcular posición del crop basado en centro de cara
                # Queremos que la cara esté centrada en el crop
                crop_x = f"iw*{kf.center_x}-{target_width}/2"
                crop_y = f"ih*{kf.center_y}-{target_height}/2"
                
                x_conditions.append(f"if(lt(t,{next_kf.time}),{crop_x}")
                y_conditions.append(f"if(lt(t,{next_kf.time}),{crop_y}")
        
        # Cerrar todos los if's
        x_expr = "".join(x_conditions) + f",iw/2-{target_width}/2" + ")" * len(x_conditions)
        y_expr = "".join(y_conditions) + f",ih/2-{target_height}/2" + ")" * len(y_conditions)
    
    # Limitar x e y para no salir del frame
    filter_str = f"crop=w={target_width}:h={target_height}:x='min(max(0,{x_expr}),iw-{target_width})':y='min(max(0,{y_expr}),ih-{target_height})'"
    
    return filter_str

def apply_auto_reframe(
    input_video: str,
    output_video: str,
    target_width: int = 720,
    target_height: int = 1280,
    ffmpeg_path: str = r"ffmpeg"
) -> str:
    """
    Aplica auto-reframe completo al video
    
    Args:
        input_video: Video de entrada
        output_video: Video de salida
        target_width: Ancho objetivo (default: 720)
        target_height: Alto objetivo (default: 1280)
    
    Returns:
        Path del video procesado
    """
    print(f"\n🎬 AUTO-REFRAME: {input_video} → {output_video}\n")
    
    # 1. Detectar caras
    keyframes = detect_face_keyframes(input_video, sample_rate=10)
    
    if not keyframes:
        print("⚠️ No se detectaron caras, usando crop centrado estático")
    else:
        # 2. Suavizar movimientos
        keyframes = smooth_keyframes(keyframes, window_size=5)
        print(f"✓ Keyframes suavizados")
    
    # 3. Generar filtro FFmpeg
    crop_filter = generate_crop_filter(keyframes, target_width, target_height)
    
    # 4. Aplicar con FFmpeg
    print("🔧 Aplicando crop dinámico...")
    
    cmd = [
        ffmpeg_path,
        '-y',
        '-i', input_video,
        '-vf', crop_filter,
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-c:a', 'copy',
        output_video
    ]
    
    subprocess.run(cmd, check=True)
    
    print(f"\n✅ AUTO-REFRAME COMPLETADO: {output_video}\n")
    return output_video

# CLI para testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python auto_reframe.py <input_video> <output_video> [width] [height]")
        print("Example: python auto_reframe.py video.mp4 output.mp4 720 1280")
        sys.exit(1)
    
    input_vid = sys.argv[1]
    output_vid = sys.argv[2]
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 720
    height = int(sys.argv[4]) if len(sys.argv) > 4 else 1280
    
    apply_auto_reframe(input_vid, output_vid, width, height)
