"""
Performance Metrics Fetcher: Obtiene Métricas Reales de Plataformas
Soporta YouTube y TikTok para análisis de performance
"""

import os
import sys
import json
from typing import Dict, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

# DB Config
DB_CONFIG = {
    "user": "n8n",
    "password": "n8n",
    "host": "localhost",
    "port": 5432,
    "database": "antigravity"
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def fetch_youtube_metrics(video_url: str) -> Optional[Dict]:
    """
    Obtiene métricas de un video de YouTube usando YouTube Data API
    
    Args:
        video_url: URL del video de YouTube
    
    Returns:
        Dict con métricas o None si falla
    """
    print(f"📊 Obteniendo métricas de YouTube: {video_url}")
    
    try:
        # Extraer video ID de la URL
        video_id = video_url.split('v=')[-1].split('&')[0]
        
        # TODO: Implementar con YouTube Data API
        # from googleapiclient.discovery import build
        # youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        # response = youtube.videos().list(
        #     part='statistics,contentDetails',
        #     id=video_id
        # ).execute()
        
        # Por ahora, mock data para testing
        metrics = {
            'platform': 'youtube',
            'views': 0,
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'watch_time_avg': 0.0,
            'retention_rate': 0.0
        }
        
        print(f"✓ Métricas obtenidas (mock): {metrics['views']} views")
        return metrics
        
    except Exception as e:
        print(f"❌ Error obteniendo métricas de YouTube: {e}")
        return None

def fetch_tiktok_metrics(video_url: str) -> Optional[Dict]:
    """
    Obtiene métricas de TikTok mediante web scraping
    
    Args:
        video_url: URL del video de TikTok
    
    Returns:
        Dict con métricas o None si falla
    """
    print(f"📊 Obteniendo métricas de TikTok: {video_url}")
    
    try:
        # TODO: Implementar scraping o TikTok API
        # from selenium import webdriver
        # driver.get(video_url)
        # Extract views, likes, comments, shares from page
        
        # Mock data
        metrics = {
            'platform': 'tiktok',
            'views': 0,
            'likes': 0,
            'comments': 0,
            'shares': 0,
            'watch_time_avg': 0.0,
            'retention_rate': 0.0
        }
        
        print(f"✓ Métricas obtenidas (mock): {metrics['views']} views")
        return metrics
        
    except Exception as e:
        print(f"❌ Error obteniendo métricas de TikTok: {e}")
        return None

def save_metrics(clip_id: str, platform: str, metrics: Dict) -> bool:
    """
    Guarda métricas en la base de datos
    """
    print(f"💾 Guardando métricas para clip {clip_id}...")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """INSERT INTO performance_metrics 
               (clip_id, platform, views, likes, comments, shares, watch_time_avg, retention_rate)
               VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s)""",
            (
                clip_id,
                platform,
                metrics.get('views', 0),
                metrics.get('likes', 0),
                metrics.get('comments', 0),
                metrics.get('shares', 0),
                metrics.get('watch_time_avg', 0.0),
                metrics.get('retention_rate', 0.0)
            )
        )
        conn.commit()
        print("✓ Métricas guardadas")
        return True
        
    except Exception as e:
        print(f"❌ Error guardando métricas: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def fetch_and_save_metrics(clip_id: str, platform: str, video_url: str) -> bool:
    """
    Pipeline completo: fetch + save
    """
    if platform == 'youtube':
        metrics = fetch_youtube_metrics(video_url)
    elif platform == 'tiktok':
        metrics = fetch_tiktok_metrics(video_url)
    else:
        print(f"⚠️ Plataforma no soportada: {platform}")
        return False
    
    if metrics:
        return save_metrics(clip_id, platform, metrics)
    
    return False

def update_all_clips_metrics():
    """
    Actualiza métricas de todos los clips publicados
    (Para ejecutar con CRON diariamente)
    """
    print("\n🔄 Actualizando métricas de todos los clips publicados...\n")
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Obtener clips con publicaciones
        cur.execute(
            """SELECT DISTINCT sp.clip_id, sp.platform, sp.video_url, c.title
               FROM scheduled_publications sp
               JOIN clips c ON sp.clip_id = c.id
               WHERE sp.status = 'published' AND sp.video_url IS NOT NULL"""
        )
        
        publications = cur.fetchall()
        print(f"✓ {len(publications)} publicaciones encontradas")
        
        for pub in publications:
            print(f"\n[Clip: {pub['title'][:30]}...]")
            fetch_and_save_metrics(
                str(pub['clip_id']),
                pub['platform'],
                pub['video_url']
            )
        
        print("\n✅ Actualización de métricas completada\n")
        
    finally:
        cur.close()
        conn.close()

# CLI
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--update-all':
            update_all_clips_metrics()
        else:
            clip_id = sys.argv[1]
            platform = sys.argv[2] if len(sys.argv) > 2 else 'youtube'
            video_url = sys.argv[3] if len(sys.argv) > 3 else ''
            
            fetch_and_save_metrics(clip_id, platform, video_url)
    else:
        print("Usage:")
        print("  python fetch_metrics.py <clip_id> <platform> <video_url>")
        print("  python fetch_metrics.py --update-all")
