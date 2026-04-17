"""
Pipeline runtime utilities:
- QuotaManager: centralized soft limits for external services
- FallbackChain: explicit ordered fallback execution
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from ..config import env_int
from ..database import get_api_usage_today

logger = logging.getLogger("pipeline-runtime")


class QuotaManager:
    """Soft quota guard based on today's recorded API usage."""

    DEFAULT_LIMITS = {
        "youtube_data_api": 250,
        "pexels": 500,
        "pixabay": 500,
        "elevenlabs": 400,
        "reddit": 1000,
        "google_trends": 1000,
    }

    def _limit_for(self, service: str) -> int:
        env_name = f"QUOTA_{service.upper()}_DAILY"
        return env_int(env_name, self.DEFAULT_LIMITS.get(service, 1000))

    def _used_for(self, service: str) -> int:
        usage_rows = get_api_usage_today(service=service)
        if not usage_rows:
            return 0
        return int(usage_rows[0].get("total_requests", 0) or 0)

    def allow(self, service: str, cost: int = 1) -> bool:
        limit = self._limit_for(service)
        used = self._used_for(service)
        allowed = used + cost <= limit
        if not allowed:
            logger.warning("Quota exceeded for %s (%s/%s)", service, used, limit)
        return allowed


class FallbackChain:
    """Runs providers in order and returns first successful value."""

    def __init__(self, name: str):
        self.name = name
        self.providers: list[tuple[str, Callable[[], Any]]] = []

    def add(self, label: str, provider: Callable[[], Any]) -> "FallbackChain":
        self.providers.append((label, provider))
        return self

    def run(self) -> tuple[str | None, Any]:
        for label, provider in self.providers:
            try:
                result = provider()
                if result:
                    return label, result
            except Exception as exc:
                logger.warning("%s provider '%s' failed: %s", self.name, label, exc)
        return None, None

