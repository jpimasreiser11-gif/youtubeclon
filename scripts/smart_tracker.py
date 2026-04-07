import cv2
import argparse
import subprocess
import json
import os
import numpy as np

def smooth_array(array, window_size=15):
    """Suaviza los movimientos de cámara usando un filtro matemático para evitar mareos"""
    if len(array) < window_size:
        return array
    return np.convolve(array, np.ones(window_size)/window_size, mode='same')

def smart_crop_video(input_path, output_path):
    print(f"Starting smart auto-camera (OpenCV): {input_path}")
    
    # Usar el clasificador de rostros de OpenCV (más fiable que MediaPipe en Windows)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    temp_video = output_path.replace('.mp4', '_temp.mp4')
    
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(json.dumps({"status": "error", "message": "No se pudo abrir el video de entrada"}))
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Queremos un video vertical 9:16 (Ej: 607x1080 si el original es 1920x1080)
    target_aspect_ratio = 9 / 16
    crop_w = int(orig_h * target_aspect_ratio)
    crop_h = orig_h
    
    # Asegurar que el recorte no sea mayor que el ancho original
    if crop_w > orig_w:
        crop_w = orig_w
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(temp_video, fourcc, fps, (crop_w, crop_h))
    
    face_x_positions = []
    
    # Pasada 1: Analizar posiciones de la cara
    print("Analyzing frames...")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        center_x = orig_w // 2 # Por defecto el centro
        if len(faces) > 0:
            # Tomar la cara más grande (asumiendo que es el protagonista)
            (x, y, w, h) = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
            center_x = x + w // 2
        
        # Limites para no salirnos de la pantalla
        center_x = max(crop_w // 2, min(orig_w - crop_w // 2, center_x))
        face_x_positions.append(center_x)
            
    cap.release()
    
    if not face_x_positions:
        print(json.dumps({"status": "error", "message": "No se detectaron frames"}))
        return

    # Aplicar suavizado de cámara cinematográfico
    smoothed_x = smooth_array(face_x_positions, window_size=20)

    # Pasada 2: Renderizar el recorte
    print("Rendering smooth reframing...")
    cap = cv2.VideoCapture(input_path)
    frame_idx = 0
    
    while cap.isOpened() and frame_idx < len(smoothed_x):
        ret, frame = cap.read()
        if not ret: break
            
        current_x = int(smoothed_x[frame_idx])
        start_x = current_x - (crop_w // 2)
        
        # Asegurar límites finales justo antes de recortar
        start_x = max(0, min(orig_w - crop_w, start_x))
        
        # Extraer la región (Recorte Vertical)
        cropped_frame = frame[0:crop_h, start_x:start_x+crop_w]
        
        # Asegurar dimensiones exactas
        if cropped_frame.shape[0] == crop_h and cropped_frame.shape[1] == crop_w:
            out.write(cropped_frame)
        else:
            # Fallback a redimensionamiento si algo falló en las dimensiones
            resized = cv2.resize(cropped_frame, (crop_w, crop_h))
            out.write(resized)
            
        frame_idx += 1
        
    cap.release()
    out.release()
    
    # Juntar el audio original con el video recortado usando FFmpeg
    print("Restoring audio...")
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", temp_video, "-i", input_path,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "23",
        "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        output_path
    ]
    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if os.path.exists(temp_video):
        os.remove(temp_video)
    
    if os.path.exists(output_path):
        print(json.dumps({"status": "success", "message": "Face tracking completed"}))
    else:
        print(json.dumps({"status": "error", "message": "Error al generar el video final con FFmpeg"}))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    smart_crop_video(args.input, args.output)
