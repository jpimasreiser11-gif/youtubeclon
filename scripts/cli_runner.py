import os
from sovereign_core import ViralEngine
import sys

def main():
    if len(sys.argv) < 2:
        print("Uso: python cli_runner.py <YOUTUBE_URL>")
        return

    url = sys.argv[1]
    api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        print("Error: Configura la variable de entorno GEMINI_API_KEY")
        print("Ejemplo (PowerShell): $env:GEMINI_API_KEY='tu_api_key'")
        return

    print("🚀 Iniciando Project Sovereign - Modo Opus Clips (Free)")
    print("-----------------------------------------------------")
    print("1. Descargando video...")
    print("2. Transcribiendo con Whisper (Local)...")
    print("3. Detectando Viralidad con Gemini...")
    print("4. Detectando Caras (MediaPipe) para Smart Crop...")
    print("5. Generando Subtítulos Dinámicos...")
    print("-----------------------------------------------------")
    
    try:
        engine = ViralEngine(api_key, output_dir="clips_virales")
        results = engine.run_pipeline(url)
        
        print("\n✅ ¡Proceso Completado!")
        for idx, res in enumerate(results):
            meta = res['metadata']
            print(f"[{idx+1}] {meta['title']} (Score: {meta['virality_score']})")
            print(f"    Archivo: {res['path']}")
            print(f"    Motivo: {meta['reason']}")
            print("-" * 30)
            
    except Exception as e:
        print(f"\n❌ Error fatal durante la ejecución: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
