"""Channels API routes."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import get_all_channels, get_channel, update_channel

router = APIRouter()


class ChannelUpdate(BaseModel):
    name: str | None = None
    voice_id: str | None = None
    frequency: str | None = None
    is_active: int | None = None
    cpm_estimate: float | None = None
    config_json: str | None = None


@router.get("/")
async def list_channels():
    """List all 6 channels with their configuration."""
    return get_all_channels()


@router.get("/{channel_id}")
async def get_channel_detail(channel_id: str):
    """Get a single channel by its slug ID."""
    ch = get_channel(channel_id)
    if not ch:
        raise HTTPException(404, f"Channel '{channel_id}' not found")
    return ch


@router.put("/{channel_id}")
async def update_channel_config(channel_id: str, body: ChannelUpdate):
    """Update channel configuration."""
    ch = get_channel(channel_id)
    if not ch:
        raise HTTPException(404, f"Channel '{channel_id}' not found")
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(400, "No fields to update")
    update_channel(channel_id, data)
    return get_channel(channel_id)
