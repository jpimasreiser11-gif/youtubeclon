"""Analytics API routes."""
from __future__ import annotations

import json
import re

from fastapi import APIRouter

from ..database import get_dashboard_stats, get_api_usage_today, get_recent_logs
from ..config import ROOT

router = APIRouter()


@router.get("/dashboard")
async def dashboard_stats():
    """Get aggregated dashboard statistics."""
    return get_dashboard_stats()


@router.get("/api-usage")
async def api_usage():
    """Get today's API usage across all services."""
    return get_api_usage_today()


@router.get("/logs")
async def recent_logs(limit: int = 100):
    """Get recent pipeline logs."""
    return get_recent_logs(limit=limit)


def _is_pid_running(pid: int) -> bool:
    try:
        import platform
        import subprocess
        if platform.system().lower().startswith("win"):
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ exit 0 }} else {{ exit 1 }}",
            ]
            return subprocess.run(cmd, capture_output=True).returncode == 0
        import os
        os.kill(pid, 0)  # POSIX-style liveness check
        return True
    except Exception:
        return False


@router.get("/agents-team")
async def agents_team_status():
    """Get visual status data for the 10-agent team screen."""
    logs_dir = ROOT / "logs"
    config_path = ROOT / "widflow-copilor-sistem" / "team-agents.config.json"
    pid_path = logs_dir / "master.pid"
    master_log = logs_dir / "master.log"
    state_path = logs_dir / "agents-state.json"

    config = {}
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))

    master_pid = None
    runner_alive = False
    if pid_path.exists():
        raw = pid_path.read_text(encoding="utf-8").strip()
        if raw.isdigit():
            master_pid = int(raw)
            runner_alive = _is_pid_running(master_pid)

    cycle_files = sorted(logs_dir.glob("agents-cycle-*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    last_cycle = cycle_files[0] if cycle_files else None
    agents: list[dict] = []
    cycle_started = None
    cycle_finished = None
    current_agent = None
    cycle_running = None

    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8-sig"))
            cycle_started = state.get("cycle_started")
            cycle_finished = state.get("cycle_finished")
            current_agent = state.get("current_agent")
            cycle_running = bool(state.get("running"))
            agents = state.get("agents", []) or []
        except Exception:
            pass

    if not agents and last_cycle and last_cycle.exists():
        text = last_cycle.read_text(encoding="utf-8", errors="ignore")
        m_start = re.search(r"^Started:\s*(.+)$", text, re.MULTILINE)
        m_finish = re.search(r"^Finished:\s*(.+)$", text, re.MULTILINE)
        cycle_started = m_start.group(1).strip() if m_start else None
        cycle_finished = m_finish.group(1).strip() if m_finish else None
        in_execution_order = False
        for line in text.splitlines():
            if line.strip() == "Execution order:":
                in_execution_order = True
                continue
            if line.strip() == "Handoffs:":
                in_execution_order = False
                continue
            if not in_execution_order:
                continue
            m = re.match(r"^\s*-\s+(.+?)\s+->\s+(.+?)\s*(?:\| (.*))?$", line)
            if m:
                agents.append({"agent_file": m.group(1), "status": m.group(2), "action": (m.group(3) or "")})

    return {
        "runner_alive": runner_alive,
        "running": cycle_running if cycle_running is not None else runner_alive,
        "master_pid": master_pid,
        "master_log_path": str(master_log),
        "last_cycle_file": str(last_cycle) if last_cycle else None,
        "last_cycle_started": cycle_started,
        "last_cycle_finished": cycle_finished,
        "current_agent": current_agent,
        "execution_order": config.get("execution_order", []),
        "handoff_rules": config.get("handoff_rules", []),
        "agents": agents,
    }


@router.get("/income")
async def income_tracking():
    """Get income tracking records."""
    tracker_path = ROOT / "monetization" / "income_tracker.json"
    if not tracker_path.exists():
        return {"records": []}
    try:
        data = json.loads(tracker_path.read_text(encoding="utf-8-sig"))
        return {"records": data if isinstance(data, list) else []}
    except Exception:
        return {"records": []}
