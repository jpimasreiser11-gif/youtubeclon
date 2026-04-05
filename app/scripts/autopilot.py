"""
Auto-Pilot: Sistema de Automatización Completo
Genera clips, añade subtítulos, SEO y publica automáticamente sin intervención humana
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Configuración DB
DB_CONFIG = {
    "user": "n8n",
    "password": "n8n",
    "host": "localhost",
    "port": 5432,
    "database": "antigravity"
}

def get_db_connection():
    """Conexión a PostgreSQL"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

async def fetch_latest_video_from_channel(channel_config: Dict) -> Optional[str]:
    """
    Obtiene el último video de un canal de YouTube
    
    Args:
        channel_config: {"channel_id": "UC...", "keywords": [...]}
    
    Returns:
        URL del último video, o None si no hay nuevos
    """
    print("📺 Buscando último video del canal...")
    
    channel_id = channel_config.get('channel_id')
    keywords = channel_config.get('keywords', [])
    
    # Usar yt-dlp para obtener últimos videos
    cmd = [
        sys.executable, '-m', 'yt_dlp',
        '--flat-playlist',
        '--print', 'url',
        '--playlist-end', '5',  # Últimos 5 videos
        f'https://www.youtube.com/channel/{channel_id}/videos'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        videos = result.stdout.strip().split('\n')
        
        if videos:
            # TODO: Verificar si ya fue procesado
            latest_url = videos[0]
            print(f"✓ Encontrado: {latest_url}")
            return latest_url
        
    except Exception as e:
        print(f"⚠️ Error obteniendo videos: {e}")
    
    return None

async def create_project_from_url(url: str, user_id: str) -> Optional[str]:
    """
    Crea un nuevo proyecto desde URL
    
    Returns:
        project_id si éxito, None si falla
    """
    print(f"🎬 Creando proyecto desde: {url}")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Crear proyecto en DB
        cur.execute(
            """INSERT INTO projects (user_id, source_video_url, project_status)
               VALUES (%s, %s, 'QUEUED') RETURNING id""",
            (user_id, url)
        )
        project_id = cur.fetchone()['id']
        conn.commit()
        
        # Ejecutar pipeline de ingestión
        script_path = Path(__file__).parent / 'ingest.py'
        cmd = [sys.executable, str(script_path), str(project_id), url]
        
        subprocess.Popen(cmd)  # Ejecutar en background
        
        print(f"✓ Proyecto creado: {project_id}")
        return str(project_id)
        
    except Exception as e:
        print(f"❌ Error creando proyecto: {e}")
        conn.rollback()
        return None
    finally:
        cur.close()
        conn.close()

async def wait_for_project_completion(project_id: str, timeout: int = 900) -> bool:
    """
    Espera a que el proyecto termine de procesarse
    
    Args:
        project_id: ID del proyecto
        timeout: Tiempo máximo de espera en segundos (default 15 min)
    
    Returns:
        True si completó, False si timeout o error
    """
    print(f"⏳ Esperando completion de proyecto {project_id}...")
    
    start_time = time.time()
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        while time.time() - start_time < timeout:
            cur.execute(
                "SELECT project_status FROM projects WHERE id = %s::uuid",
                (project_id,)
            )
            result = cur.fetchone()
            
            if not result:
                return False
            
            status = result['project_status']
            
            if status == 'COMPLETED':
                print("✓ Proyecto completado!")
                return True
            elif status == 'FAILED':
                print("❌ Proyecto falló")
                return False
            
            # Esperar 10 segundos antes de verificar de nuevo
            await asyncio.sleep(10)
        
        print("⏱️ Timeout esperando completion")
        return False
        
    finally:
        cur.close()
        conn.close()

async def get_filtered_clips(
    project_id: str,
    min_score: int = 85,
    categories: List[str] = None
) -> List[Dict]:
    """
    Obtiene clips filtrados por score y categoría
    """
    print(f"🔍 Obteniendo clips (score >= {min_score})...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        query = """
            SELECT * FROM clips 
            WHERE project_id = %s::uuid 
            AND virality_score >= %s
        """
        params = [project_id, min_score]
        
        if categories:
            query += " AND category = ANY(%s)"
            params.append(categories)
        
        query += " ORDER BY virality_score DESC"
        
        cur.execute(query, params)
        clips = cur.fetchall()
        
        print(f"✓ {len(clips)} clips encontrados")
        return clips
        
    finally:
        cur.close()
        conn.close()

async def process_clip_with_subtitle_and_seo(
    clip_id: str,
    subtitle_preset: str = 'tiktok',
    generate_seo: bool = True
) -> bool:
    """
    Procesa un clip: añade subtítulos + genera SEO
    """
    print(f"⚙️ Procesando clip {clip_id}...")
    
    try:
        # 1. Añadir subtítulos
        from add_subtitles_advanced import add_advanced_subtitles
        
        video_path = f"storage/clips/{clip_id}.mp4"
        audio_path = f"storage/clips/{clip_id}.mp3"
        output_path = f"storage/subtitled/{clip_id}.mp4"
        
        # TODO: Ejecutar add_advanced_subtitles
        # await add_advanced_subtitles(video_path, audio_path, output_path, subtitle_preset)
        
        # 2. Generar SEO si está habilitado
        if generate_seo:
            from auto_seo import generate_seo_metadata
            
            conn = get_db_connection()
            cur = conn.cursor()
            
            cur.execute(
                "SELECT hook_description, payoff_description, category, start_time, end_time FROM clips WHERE id = %s::uuid",
                (clip_id,)
            )
            clip = cur.fetchone()
            
            if clip:
                metadata = await generate_seo_metadata(
                    clip['hook_description'],
                    clip['payoff_description'],
                    clip['category'],
                    clip['end_time'] - clip['start_time']
                )
                
                cur.execute(
                    """UPDATE clips 
                       SET title_generated = %s, 
                           description_generated = %s, 
                           hashtags = %s 
                       WHERE id = %s::uuid""",
                    (metadata['title'], metadata['description'], metadata['hashtags'], clip_id)
                )
                conn.commit()
            
            cur.close()
            conn.close()
        
        print("✓ Clip procesado")
        return True
        
    except Exception as e:
        print(f"❌ Error procesando clip: {e}")
        return False

async def schedule_publication(
    clip_id: str,
    platform: str,
    scheduled_time: datetime,
    title: str = None,
    description: str = None
) -> bool:
    """
    Programa una publicación futura
    """
    print(f"📅 Programando publicación: {platform} @ {scheduled_time}")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """INSERT INTO scheduled_publications 
               (clip_id, platform, scheduled_at, status, title)
               VALUES (%s::uuid, %s, %s, 'pending', %s)""",
            (clip_id, platform, scheduled_time, title or 'Auto-generated')
        )
        conn.commit()
        print("✓ Publicación programada")
        return True
        
    except Exception as e:
        print(f"❌ Error programando: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def calculate_next_publish_slot(
    profile: Dict,
    existing_publications: List
) -> datetime:
    """
    Calcula el próximo slot disponible para publicar
    respetando posts_per_day y schedule_times
    """
    posts_per_day = profile.get('posts_per_day', 3)
    schedule_times = profile.get('schedule_times', ['09:00', '14:00', '19:00'])
    
    # Obtener publicaciones de hoy
    today = datetime.now().date()
    today_posts = [p for p in existing_publications if p['scheduled_at'].date() == today]
    
    if len(today_posts) >= posts_per_day:
        # Ya alcanzamos el límite de hoy, programar para mañana
        next_day = today + timedelta(days=1)
        hour, minute = map(int, schedule_times[0].split(':'))
        return datetime.combine(next_day, datetime.min.time().replace(hour=hour, minute=minute))
    
    # Buscar próximo slot disponible hoy
    now = datetime.now()
    for time_str in schedule_times:
        hour, minute = map(int, time_str.split(':'))
        slot_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if slot_time > now:
            # Verificar si este slot ya está ocupado
            slot_occupied = any(
                abs((p['scheduled_at'] - slot_time).total_seconds()) < 300  # 5 min tolerance
                for p in today_posts
            )
            
            if not slot_occupied:
                return slot_time
    
    # Si llegamos aquí, usar mañana
    tomorrow = today + timedelta(days=1)
    hour, minute = map(int, schedule_times[0].split(':'))
    return datetime.combine(tomorrow, datetime.min.time().replace(hour=hour, minute=minute))

async def run_automation_profile(profile_id: str) -> Dict[str, Any]:
    """
    Ejecuta un perfil de automatización completo
    
    Returns:
        Resultado del run con estadísticas
    """
    print(f"\n{'='*60}")
    print(f"🤖 AUTO-PILOT: Ejecutando perfil {profile_id}")
    print(f"{'='*60}\n")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # 1. Obtener configuración del perfil
        cur.execute(
            "SELECT * FROM automation_profiles WHERE id = %s::uuid",
            (profile_id,)
        )
        profile = cur.fetchone()
        
        if not profile or not profile['active']:
            return {"error": "Profile not found or inactive"}
        
        # 2. Crear run en DB
        cur.execute(
            """INSERT INTO automation_runs (profile_id, status)
               VALUES (%s::uuid, 'running') RETURNING id""",
            (profile_id,)
        )
        run_id = cur.fetchone()['id']
        conn.commit()
        
        clips_generated = 0
        clips_published = 0
        
        try:
            # 3. Obtener último video de la fuente
            source_config = profile['source_config']
            video_url = await fetch_latest_video_from_channel(source_config)
            
            if not video_url:
                raise Exception("No se encontró video nuevo")
            
            # 4. Crear proyecto
            project_id = await create_project_from_url(video_url, profile['user_id'])
            
            if not project_id:
                raise Exception("Error creando proyecto")
            
            # 5. Esperar completion (max 15 min)
            completed = await wait_for_project_completion(project_id, timeout=900)
            
            if not completed:
                raise Exception("Proyecto no completó a tiempo")
            
            # 6. Obtener clips filtrados
            clips = await get_filtered_clips(
                project_id,
                min_score=profile['min_virality_score'],
                categories=profile.get('categories')
            )
            
            clips_generated = len(clips)
            
            # 7. Procesar cada clip
            for clip in clips:
                # Subtítulos + SEO
                success = await process_clip_with_subtitle_and_seo(
                    str(clip['id']),
                    subtitle_preset=profile['subtitle_preset'],
                    generate_seo=profile['auto_seo']
                )
                
                if not success:
                    continue
                
                # Programar publicaciones
                existing_pubs = []  # TODO: Fetch existing
                
                for platform in profile['platforms']:
                    next_time = calculate_next_publish_slot(profile, existing_pubs)
                    
                    await schedule_publication(
                        str(clip['id']),
                        platform,
                        next_time,
                        title=clip.get('title_generated')
                    )
                    
                    clips_published += 1
                    existing_pubs.append({'scheduled_at': next_time})
            
            # 8. Marcar run como completado
            cur.execute(
                """UPDATE automation_runs 
                   SET status = 'completed', 
                       clips_generated = %s,
                       clips_published = %s,
                       completed_at = NOW()
                   WHERE id = %s::uuid""",
                (clips_generated, clips_published, run_id)
            )
            
            # Actualizar last_run del profile
            cur.execute(
                "UPDATE automation_profiles SET last_run = NOW() WHERE id = %s::uuid",
                (profile_id,)
            )
            
            conn.commit()
            
            result = {
                "run_id": str(run_id),
                "status": "completed",
                "clips_generated": clips_generated,
                "clips_published": clips_published
            }
            
            print(f"\n✅ AUTO-PILOT COMPLETADO")
            print(f"   Clips generados: {clips_generated}")
            print(f"   Clips publicados: {clips_published}")
            
            return result
            
        except Exception as e:
            # Marcar run como failed
            cur.execute(
                """UPDATE automation_runs 
                   SET status = 'failed', 
                       error_message = %s,
                       completed_at = NOW()
                   WHERE id = %s::uuid""",
                (str(e), run_id)
            )
            conn.commit()
            
            print(f"❌ AUTO-PILOT FALLÓ: {e}")
            return {"error": str(e)}
            
    finally:
        cur.close()
        conn.close()

async def run_all_active_profiles():
    """
    Ejecuta todos los perfiles activos
    (Para ser llamado por CRON cada X horas)
    """
    print("🔄 Verificando perfiles activos...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "SELECT id FROM automation_profiles WHERE active = true"
        )
        profiles = cur.fetchall()
        
        print(f"✓ {len(profiles)} perfiles activos encontrados")
        
        for profile in profiles:
            await run_automation_profile(str(profile['id']))
            
    finally:
        cur.close()
        conn.close()

# CLI
if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Ejecutar perfil específico
        profile_id = sys.argv[1]
        asyncio.run(run_automation_profile(profile_id))
    else:
        # Ejecutar todos los activos
        asyncio.run(run_all_active_profiles())
