"""Pipeline API routes — trigger video generation, check status."""
from __future__ import annotations

import asyncio
import threading
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from ..database import (
    get_channel, get_all_channels, get_recent_logs, get_trends,
    log_pipeline_step
)

router = APIRouter()
logger = logging.getLogger("pipeline-api")

# ── WebSocket connections for real-time updates ──────────────
_ws_clients: list[WebSocket] = []


async def broadcast(data: dict) -> None:
    """Send update to all connected WebSocket clients."""
    import json
    msg = json.dumps(data)
    disconnected = []
    for ws in _ws_clients:
        try:
            await ws.send_text(msg)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        _ws_clients.remove(ws)


@router.websocket("/ws")
async def pipeline_ws(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(_ws_clients)}")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _ws_clients.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(_ws_clients)}")


# ── Pipeline trigger ─────────────────────────────────────────
class GenerateRequest(BaseModel):
    channel_id: str
    topic: str | None = None
    upload: bool = False


_running_jobs: dict[str, str] = {}  # channel_id -> status


@router.post("/generate")
async def trigger_generation(body: GenerateRequest):
    """Start video generation for a channel. Runs in background thread."""
    ch = get_channel(body.channel_id)
    if not ch:
        raise HTTPException(404, f"Channel '{body.channel_id}' not found")

    if body.channel_id in _running_jobs and _running_jobs[body.channel_id] == "running":
        raise HTTPException(409, f"Pipeline already running for '{body.channel_id}'")

    _running_jobs[body.channel_id] = "running"
    log_pipeline_step(ch["id"], None, "pipeline_start", "running",
                      f"Starting pipeline for {ch['name']}")

    def _run():
        try:
            from ..pipeline.orchestrator import run_single_channel
            result = run_single_channel(body.channel_id, topic=body.topic, upload=body.upload)
            _running_jobs[body.channel_id] = "done"
            logger.info(f"Pipeline completed for {body.channel_id}: {result.get('status')}")
        except Exception as exc:
            _running_jobs[body.channel_id] = "error"
            logger.error(f"Pipeline failed for {body.channel_id}: {exc}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {
        "message": f"Pipeline started for '{ch['name']}'",
        "channel_id": body.channel_id,
        "topic": body.topic,
        "status": "running",
    }


@router.get("/status")
async def pipeline_status():
    """Get current pipeline status for all channels."""
    return {
        "running_jobs": _running_jobs,
        "recent_logs": get_recent_logs(limit=50),
    }


@router.get("/trends/{channel_id}")
async def get_channel_trends(channel_id: str, limit: int = 10):
    """Get trending topics for a channel."""
    ch = get_channel(channel_id)
    if not ch:
        raise HTTPException(404, f"Channel '{channel_id}' not found")
    trends = get_trends(channel_db_id=ch["id"], limit=limit)
    return {"channel": channel_id, "trends": trends}


@router.post("/find-trends/{channel_id}")
async def trigger_trend_finding(channel_id: str):
    """Find trending topics for a specific channel."""
    ch = get_channel(channel_id)
    if not ch:
        raise HTTPException(404, f"Channel '{channel_id}' not found")

    def _run():
        try:
            from ..pipeline.trend_finder import find_trending_topics
            find_trending_topics(ch)
        except Exception as exc:
            logger.error(f"Trend finding failed for {channel_id}: {exc}")

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    return {"message": f"Trend finding started for '{ch['name']}'", "status": "running"}
