"""
API Routes — Scheduler
Endpoints to list, add, and cancel scheduled publish jobs.
"""
from __future__ import annotations

import logging
from typing import List
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from ..database import get_db, dicts_from_rows, get_video
from ..pipeline.youtube_publisher import upload_video_to_youtube

router = APIRouter(prefix="/api/schedule", tags=["schedule"])
logger = logging.getLogger("youtube-auto-pro.api.schedule")

class ScheduleAddRequest(BaseModel):
    video_id: int
    channel_id: int
    scheduled_at: str  # ISO Format

@router.get("/")
async def get_schedules(status: str = 'pending'):
    query = """
        SELECT s.id as schedule_id, s.scheduled_at, s.status, s.created_at,
               v.id as video_id, v.title, v.thumbnail_path, v.status as video_status,
               c.name as channel_name, c.channel_id as channel_slug
        FROM schedule s
        JOIN videos v ON s.video_id = v.id
        JOIN channels c ON s.channel_id = c.id
    """
    params = []
    if status != 'all':
        query += " WHERE s.status = ?"
        params.append(status)
        
    query += " ORDER BY s.scheduled_at ASC"
    
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        
    return {"schedules": dicts_from_rows(rows)}

@router.post("/add")
async def add_schedule(req: ScheduleAddRequest):
    # Verify video exists
    video = get_video(req.video_id)
    if not video:
        raise HTTPException(404, "Video not found")
        
    with get_db() as conn:
        conn.execute(
            "INSERT INTO schedule (channel_id, video_id, scheduled_at, status) VALUES (?, ?, ?, 'pending')",
            (req.channel_id, req.video_id, req.scheduled_at)
        )
        
    return {"status": "ok", "message": "Video scheduled successfully."}

@router.delete("/{schedule_id}")
async def cancel_schedule(schedule_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM schedule WHERE id = ?", (schedule_id,))
    return {"status": "ok", "message": "Schedule canceled."}

def _bg_publish_now(video_id: int, channel_id: int):
    video_data = get_video(video_id)
    if video_data:
        # Mark schedule as processing if exists
        with get_db() as conn:
            conn.execute("UPDATE schedule SET status = 'processing' WHERE video_id = ? AND status = 'pending'", (video_id,))
            
        success = upload_video_to_youtube(video_data, channel_id)
        
        with get_db() as conn:
            if success:
                conn.execute("UPDATE schedule SET status = 'completed' WHERE video_id = ? AND status = 'processing'", (video_id,))
            else:
                conn.execute("UPDATE schedule SET status = 'error' WHERE video_id = ? AND status = 'processing'", (video_id,))

@router.post("/publish-now/{video_id}")
async def publish_now(video_id: int, bg: BackgroundTasks):
    video = get_video(video_id)
    if not video:
        raise HTTPException(404, "Video not found")
        
    channel_db_id = video["channel_id"]
    bg.add_task(_bg_publish_now, video_id, channel_db_id)
    return {"status": "started", "message": "Enviado a cola de subida inmediatamente."}
