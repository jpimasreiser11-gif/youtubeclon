import os
import shutil
import psycopg2
import sys
import time
from dotenv import load_dotenv

# FIX: Forzar UTF-8 en Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Configuración
load_dotenv('.env')
storage_base = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'storage'))

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        dbname=os.getenv('POSTGRES_DB', 'antigravity'),
        user=os.getenv('POSTGRES_USER', 'n8n'),
        password=os.getenv('POSTGRES_PASSWORD', 'n8n')
    )

def cleanup():
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("[RUN] Iniciando limpieza de almacenamiento...")
    
    # Obtener IDs activos
    cur.execute("SELECT id::text FROM projects")
    active_project_ids = {row[0] for row in cur.fetchall()}
    
    cur.execute("SELECT id::text FROM clips")
    active_clip_ids = {row[0] for row in cur.fetchall()}
    
    cur.close()
    conn.close()
    
    print(f"[SUCCESS] Proyectos activos en DB: {len(active_project_ids)}")
    print(f"[SUCCESS] Clips activos en DB: {len(active_clip_ids)}")
    
    deleted_files = 0
    deleted_dirs = 0
    bytes_freed = 0

    def _safe_unlink(filepath, label='archivo'):
        nonlocal deleted_files, bytes_freed
        try:
            if os.path.exists(filepath):
                bytes_freed += os.path.getsize(filepath)
                os.remove(filepath)
                deleted_files += 1
                print(f"[DELETE] Eliminado {label}: {os.path.basename(filepath)}")
        except Exception as e:
            print(f"[WARN] No se pudo eliminar {filepath}: {e}")

    def _clip_id_from_filename(filename):
        base = os.path.splitext(filename)[0]
        # clipid, clipid_vertical, clipid_subtitled
        return base.split('_')[0]
    
    # 1. Limpiar temp/ (Carpetas de proyectos)
    temp_dir = os.path.join(storage_base, 'temp')
    if os.path.exists(temp_dir):
        for dirname in os.listdir(temp_dir):
            dir_path = os.path.join(temp_dir, dirname)
            if os.path.isdir(dir_path) and dirname not in active_project_ids:
                size = sum(os.path.getsize(os.path.join(dirpath, filename)) for dirpath, _, filenames in os.walk(dir_path) for filename in filenames)
                shutil.rmtree(dir_path)
                bytes_freed += size
                deleted_dirs += 1
                print(f"[DELETE] Eliminada carpeta huérfana temporal: {dirname}")

    # 2. Limpiar clips/ (Archivos de clips)
    clips_dir = os.path.join(storage_base, 'clips')
    if os.path.exists(clips_dir):
        for filename in os.listdir(clips_dir):
            if not filename.endswith('.mp4'): continue
            clip_id = filename.replace('.mp4', '')
            if clip_id not in active_clip_ids:
                _safe_unlink(os.path.join(clips_dir, filename), 'clip huérfano')
                
    # 3. Limpiar processed/
    processed_dir = os.path.join(storage_base, 'processed')
    if os.path.exists(processed_dir):
        for filename in os.listdir(processed_dir):
            if not filename.endswith('.mp4'): continue
            clip_id = _clip_id_from_filename(filename)
            if clip_id not in active_clip_ids:
                _safe_unlink(os.path.join(processed_dir, filename), 'video procesado huérfano')
                
    # 4. Limpiar thumbnails/
    thumbs_dir = os.path.join(storage_base, 'thumbnails')
    if os.path.exists(thumbs_dir):
        for filename in os.listdir(thumbs_dir):
            if not (filename.endswith('.jpg') or filename.endswith('.png')):
                continue
            clip_id = os.path.splitext(filename)[0]
            if clip_id not in active_clip_ids:
                _safe_unlink(os.path.join(thumbs_dir, filename), 'thumbnail huérfano')

    # 5. Limpiar subtitled/
    subtitled_dir = os.path.join(storage_base, 'subtitled')
    if os.path.exists(subtitled_dir):
        for filename in os.listdir(subtitled_dir):
            if not filename.endswith('.mp4'):
                continue
            clip_id = _clip_id_from_filename(filename)
            if clip_id not in active_clip_ids:
                _safe_unlink(os.path.join(subtitled_dir, filename), 'subtitled huérfano')

    # 6. Limpiar previews/
    previews_dir = os.path.join(storage_base, 'previews')
    if os.path.exists(previews_dir):
        for filename in os.listdir(previews_dir):
            if not filename.endswith('.mp4'):
                continue
            clip_id = _clip_id_from_filename(filename)
            if clip_id not in active_clip_ids:
                _safe_unlink(os.path.join(previews_dir, filename), 'preview huérfano')

    # 7. Limpiar enhanced/
    enhanced_dir = os.path.join(storage_base, 'enhanced')
    if os.path.exists(enhanced_dir):
        for filename in os.listdir(enhanced_dir):
            if not filename.endswith('.mp4'):
                continue
            clip_id = _clip_id_from_filename(filename)
            if clip_id not in active_clip_ids:
                _safe_unlink(os.path.join(enhanced_dir, filename), 'enhanced huérfano')

    # 8. Limpiar source/ por project_id
    source_dir = os.path.join(storage_base, 'source')
    if os.path.exists(source_dir):
        for filename in os.listdir(source_dir):
            if not filename.endswith('.mp4'):
                continue
            base = os.path.splitext(filename)[0]
            project_id = base[:-7] if base.endswith('_master') else base
            if project_id not in active_project_ids:
                _safe_unlink(os.path.join(source_dir, filename), 'source huérfano')

    # 9. Limpiar cache vieja (videos/transcripts > 30 dias)
    cache_dir = os.path.join(storage_base, 'cache')
    if os.path.exists(cache_dir):
        cutoff = time.time() - (30 * 24 * 60 * 60)
        for root, _, files in os.walk(cache_dir):
            for filename in files:
                filepath = os.path.join(root, filename)
                try:
                    mtime = os.path.getmtime(filepath)
                    if mtime < cutoff:
                        _safe_unlink(filepath, 'cache vieja')
                except Exception:
                    continue
                
    mb_freed = bytes_freed / (1024 * 1024)
    print("\n===============================")
    print("[SUCCESS] Limpieza completada!")
    print(f"Archivos eliminados: {deleted_files}")
    print(f"Carpetas eliminadas: {deleted_dirs}")
    print(f"Espacio liberado: {mb_freed:.2f} MB")
    print("===============================\n")

if __name__ == '__main__':
    cleanup()
