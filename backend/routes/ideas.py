"""
API Routes — Idea Engine
Endpoints para generar, listar, filtrar y gestionar ideas virales.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from ..pipeline.idea_engine import (
    generate_ideas_for_channel,
    generate_ideas_all_channels,
    get_ideas,
    get_idea_stats,
    mark_idea_used,
    delete_idea,
    NICHE_DNA,
    STRATEGIES,
)

router = APIRouter(prefix="/api/ideas", tags=["ideas"])


# ── Request/Response Models ──────────────────────────────────

class GenerateRequest(BaseModel):
    channel_id: str
    strategies: list[str] | None = None
    ideas_per_strategy: int = 5

class GenerateAllRequest(BaseModel):
    ideas_per_strategy: int = 3


# ── Background task storage ──────────────────────────────────

_generation_status: dict = {"running": False, "last_result": None}


def _run_generation(channel_id: str, strategies, ideas_per_strategy):
    global _generation_status
    _generation_status["running"] = True
    try:
        result = generate_ideas_for_channel(channel_id, strategies, ideas_per_strategy)
        _generation_status["last_result"] = result
    except Exception as exc:
        _generation_status["last_result"] = {"error": str(exc)}
    finally:
        _generation_status["running"] = False


def _run_generation_all(ideas_per_strategy):
    global _generation_status
    _generation_status["running"] = True
    try:
        result = generate_ideas_all_channels(ideas_per_strategy)
        _generation_status["last_result"] = result
    except Exception as exc:
        _generation_status["last_result"] = {"error": str(exc)}
    finally:
        _generation_status["running"] = False


# ── Endpoints ────────────────────────────────────────────────

@router.post("/generate")
async def api_generate_ideas(req: GenerateRequest, bg: BackgroundTasks):
    """Generate ideas for a specific channel (runs in background)."""
    if req.channel_id not in NICHE_DNA:
        raise HTTPException(400, f"Unknown channel_id. Valid: {list(NICHE_DNA.keys())}")
    if _generation_status["running"]:
        raise HTTPException(409, "Idea generation already in progress")

    bg.add_task(_run_generation, req.channel_id, req.strategies, req.ideas_per_strategy)
    return {
        "status": "started",
        "message": f"Generating ideas for {req.channel_id} — this takes ~30-60 seconds",
        "channel_id": req.channel_id,
        "strategies": req.strategies or list(STRATEGIES.keys()),
    }


@router.post("/generate-all")
async def api_generate_all(req: GenerateAllRequest, bg: BackgroundTasks):
    """Generate ideas for ALL 6 channels."""
    if _generation_status["running"]:
        raise HTTPException(409, "Idea generation already in progress")

    bg.add_task(_run_generation_all, req.ideas_per_strategy)
    return {
        "status": "started",
        "message": "Generating ideas for all 6 channels — this takes ~3-5 minutes",
        "channels": list(NICHE_DNA.keys()),
    }


@router.get("/status")
async def api_generation_status():
    """Check if idea generation is running and get last result."""
    return {
        "running": _generation_status["running"],
        "last_result": _generation_status["last_result"],
    }


@router.get("/list")
async def api_list_ideas(
    channel: str | None = Query(None, description="Filter by channel_id"),
    strategy: str | None = Query(None, description="Filter by strategy"),
    unused_only: bool = Query(False, description="Only show unused ideas"),
    limit: int = Query(50, ge=1, le=200),
):
    """List ideas with optional filters."""
    ideas = get_ideas(channel_id=channel, strategy=strategy,
                      unused_only=unused_only, limit=limit)
    return {"total": len(ideas), "ideas": ideas}


@router.get("/stats")
async def api_idea_stats():
    """Get idea pool statistics."""
    return get_idea_stats()


@router.get("/strategies")
async def api_list_strategies():
    """List all available generation strategies."""
    return {
        key: {
            "name_es": s["name_es"],
            "name_en": s["name_en"],
            "description": s["description"],
        }
        for key, s in STRATEGIES.items()
    }


@router.get("/channels")
async def api_list_channels_dna():
    """List channel niche DNA (themes, formulas, competitors)."""
    return {
        key: {
            "name": dna["name"],
            "lang": dna["lang"],
            "core_themes": dna["core_themes"],
            "viral_formulas": dna["viral_formulas"],
            "competitor_channels": dna["competitor_channels"],
        }
        for key, dna in NICHE_DNA.items()
    }


@router.post("/{idea_id}/use")
async def api_mark_used(idea_id: int):
    """Mark an idea as used (converted to video)."""
    mark_idea_used(idea_id)
    return {"status": "ok", "idea_id": idea_id, "message": "Idea marked as used"}


@router.delete("/{idea_id}")
async def api_delete_idea(idea_id: int):
    """Delete a rejected idea."""
    delete_idea(idea_id)
    return {"status": "ok", "idea_id": idea_id, "message": "Idea deleted"}
