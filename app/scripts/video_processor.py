"""
Advanced Video Processing: Vertical Crop with Blur Background
Creates 9:16 vertical videos from horizontal source with blurred background
"""

import os
import sys
import subprocess
import argparse

def create_vertical_clip_with_blur(input_path, output_path, start_time, end_time):
    """
    Crea un clip vertical 9:16 con fondo difuminado
    
    Args:
        input_path: Ruta del video original
        output_path: Ruta para guardar el clip vertical
        start_time: Tiempo de inicio en segundos
        end_time: Tiempo de fin en segundos
    
    Proceso:
    1. Extrae el clip del video original
    2. Crea dos capas:
       - Fondo: Video escalado y difuminado (blur)
       - Principal: Video centrado manteniendo aspect ratio
    3. Combina ambas capas
    """
    
    # Find FFmpeg robustly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    FFMPEG_PATH = os.path.join(project_root, "data", "ffmpeg.exe")
    if not os.path.exists(FFMPEG_PATH):
        import shutil
        sys_ffmpeg = shutil.which("ffmpeg")
        FFMPEG_PATH = sys_ffmpeg if sys_ffmpeg else "ffmpeg"
    
    if not os.path.exists(input_path):
        print(f"❌ Error: Input video not found at {input_path}")
        return False
    
    print(f"🎬 Creating vertical clip with blur background...")
    print(f"📹 Input: {input_path}")
    print(f"⏰ Duration: {start_time}s - {end_time}s")
    
    # Calcular duración
    duration = end_time - start_time
    
    # Filter complex para crear video vertical con blur
    # Este es el filtro usado por apps profesionales como Opus Clips
    filter_complex = (
        # Capa de fondo (blur)
        "[0:v]scale=720:1280:force_original_aspect_ratio=increase,"
        "crop=720:1280,"
        "boxblur=30:5[bg];"
        
        # Capa principal (video centrado)
        "[0:v]scale=720:1280:force_original_aspect_ratio=decrease,"
        "pad=720:1280:(ow-iw)/2:(oh-ih)/2:black[fg];"
        
        # Combinar capas
        "[bg][fg]overlay=0:0"
    )
    
    print("⚙️ Processing with FFmpeg...")
    
    try:
        subprocess.run([
            FFMPEG_PATH, '-y',
            '-ss', str(start_time),
            '-i', input_path,
            '-t', str(duration),
            '-filter_complex', filter_complex,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-r', '30',  # 30 FPS
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '44100',
            output_path
        ], check=True)
        
        print(f"✅ Vertical clip created successfully!")
        print(f"💾 Saved to: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error: {e}")
        return False

def optimize_for_platform(input_path, output_path, platform='tiktok'):
    """
    Optimiza el video para una plataforma específica
    
    Args:
        platform: 'tiktok', 'youtube_shorts', o 'instagram_reels'
    """
    
    # Find FFmpeg robustly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    FFMPEG_PATH = os.path.join(project_root, "data", "ffmpeg.exe")
    if not os.path.exists(FFMPEG_PATH):
        import shutil
        sys_ffmpeg = shutil.which("ffmpeg")
        FFMPEG_PATH = sys_ffmpeg if sys_ffmpeg else "ffmpeg"
    
    # Configuraciones por plataforma
    platform_configs = {
        'tiktok': {
            'resolution': '720:1280',
            'bitrate': '2500k',
            'audio_bitrate': '128k',
            'fps': '30'
        },
        'youtube_shorts': {
            'resolution': '1080:1920',
            'bitrate': '5000k',
            'audio_bitrate': '192k',
            'fps': '30'
        },
        'instagram_reels': {
            'resolution': '1080:1920',
            'bitrate': '3500k',
            'audio_bitrate': '128k',
            'fps': '30'
        }
    }
    
    config = platform_configs.get(platform, platform_configs['tiktok'])
    
    print(f"🎯 Optimizing for {platform}...")
    
    try:
        subprocess.run([
            FFMPEG_PATH, '-y',
            '-i', input_path,
            '-vf', f'scale={config["resolution"]}:force_original_aspect_ratio=decrease,pad={config["resolution"]}:(ow-iw)/2:(oh-ih)/2',
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-b:v', config['bitrate'],
            '-r', config['fps'],
            '-c:a', 'aac',
            '-b:a', config['audio_bitrate'],
            output_path
        ], check=True)
        
        print(f"✅ Optimized for {platform}!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error optimizing: {e}")
        return False

def compress_for_gemini(input_path, output_path):
    """
    Comprime video para análisis de IA (reduce costo)
    Gemini no necesita 4K para entender el contenido
    """
    
    # Find FFmpeg robustly
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    FFMPEG_PATH = os.path.join(project_root, "data", "ffmpeg.exe")
    if not os.path.exists(FFMPEG_PATH):
        import shutil
        sys_ffmpeg = shutil.which("ffmpeg")
        FFMPEG_PATH = sys_ffmpeg if sys_ffmpeg else "ffmpeg"
    
    print("🗜️ Compressing video for AI analysis...")
    
    try:
        subprocess.run([
            FFMPEG_PATH, '-y',
            '-i', input_path,
            '-vf', 'scale=480:-1',  # 480p width
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-crf', '28',  # Más compresión
            '-b:v', '500k',
            '-b:a', '64k',
            output_path
        ], check=True)
        
        original_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
        compressed_size = os.path.getsize(output_path) / (1024 * 1024)
        
        print(f"✅ Compressed: {original_size:.1f}MB → {compressed_size:.1f}MB")
        print(f"💰 Cost reduction: {((original_size - compressed_size) / original_size * 100):.0f}%")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error compressing: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced video processing")
    parser.add_argument("--input", required=True, help="Input video path")
    parser.add_argument("--output", required=True, help="Output video path")
    parser.add_argument("--mode", default="vertical", choices=['vertical', 'optimize', 'compress'])
    parser.add_argument("--start", type=float, help="Start time in seconds (for vertical mode)")
    parser.add_argument("--end", type=float, help="End time in seconds (for vertical mode)")
    parser.add_argument("--platform", default="tiktok", help="Platform for optimization")
    
    args = parser.parse_args()
    
    if args.mode == 'vertical':
        if not args.start or not args.end:
            print("❌ Error: --start and --end required for vertical mode")
            sys.exit(1)
        result = create_vertical_clip_with_blur(args.input, args.output, args.start, args.end)
    
    elif args.mode == 'optimize':
        result = optimize_for_platform(args.input, args.output, args.platform)
    
    elif args.mode == 'compress':
        result = compress_for_gemini(args.input, args.output)
    
    sys.exit(0 if result else 1)
