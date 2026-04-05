import os
import sys
import subprocess
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def run_script(script_name, args):
    cmd = ["python", f"scripts/{script_name}"] + args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_name}: {result.stderr}")
        print(f"Output: {result.stdout}")
        return False
    return True

def main():
    print("=== Flujo Viral Pro: Inicio de Ciclo ===")
    
    # 1. Simular Ideacion
    print("\n[1] Fase de Ideación (Trend Hunter)")
    # En produccion esto consultaria a Gemini
    idea = {
        "nicho": "Datos Curiosos del Espacio",
        "script_text": "Sabias que en el espacio nadie puede oir tus gritos? Esto es porque el sonido necesita un medio para viajar, como el aire. En el vacio, es silencio total. Dale like para mas datos oscuros.",
        "keywords": "space dark universe"
    }
    print(f"Idea Generada: {idea['nicho']}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("temp", exist_ok=True)
    
    audio_file = f"temp/audio_{timestamp}.mp3"
    video_stock = f"temp/stock_{timestamp}.mp4"
    final_video = f"output_{timestamp}.mp4"

    # 2. TTS
    print("\n[2] Fase de Audio (TTS)")
    if not run_script("tts.py", ["--text", idea["script_text"], "--output", audio_file]):
        return

    # 3. Video
    print("\n[3] Fase de Visuales (Fetch)")
    if not run_script("fetch_video.py", ["--keywords", idea["keywords"], "--output", video_stock]):
        print("Warning: Fetch falló (probablemente falta API Key).")
    
    # 4. Render
    print("\n[4] Fase de Renderizado")
    # Check if files exist
    if os.path.exists(audio_file) and os.path.exists(video_stock) and os.path.getsize(video_stock) > 0:
         if not run_script("render.py", ["--audio", audio_file, "--video", video_stock, "--output", final_video]):
             print("Fallo en renderizado.")
    else:
        print("Saltando renderizado real (faltan recursos).")

    print(f"\nCiclo finalizado. Video potencial: {final_video}")

if __name__ == "__main__":
    main()
