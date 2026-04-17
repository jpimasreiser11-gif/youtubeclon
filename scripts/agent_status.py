#!/usr/bin/env python3
"""
agent_status.py — Sistema de estado en tiempo real de los 10 agentes
Uso: python scripts/agent_status.py
     python scripts/agent_status.py --json   (output para otras apps)
     python scripts/agent_status.py --once   (mostrar una vez y salir)
"""

import os, json, time, sys, glob, subprocess, ctypes
from datetime import datetime, timezone
from pathlib import Path

MODE = sys.argv[1] if len(sys.argv) > 1 else "--watch"

AGENTS = {
    "00": {"name": "Patriarch",      "emoji": "👴", "output": "diary/"},
    "01": {"name": "Researcher",     "emoji": "🔍", "output": "research/daily-reports/"},
    "02": {"name": "Content Forge",  "emoji": "✍️ ", "output": "content_calendars/"},
    "03": {"name": "Code Sentinel",  "emoji": "🛡️ ", "output": "code-reviews/"},
    "04": {"name": "SEO Engineer",   "emoji": "📈", "output": "seo/"},
    "05": {"name": "Quality Gate",   "emoji": "✅", "output": "quality-reports/"},
    "06": {"name": "Money Finder",   "emoji": "💰", "output": "monetization/"},
    "07": {"name": "Data Analyst",   "emoji": "📊", "output": "analytics/"},
    "08": {"name": "Fixer",          "emoji": "🔧", "output": "logs/fixes/"},
    "09": {"name": "Trend Hunter",   "emoji": "🌊", "output": ".copilot/agents/agent-09-trends/"},
    "10": {"name": "Scheduler",      "emoji": "🗓️ ", "output": "briefings/"},
    "11": {"name": "UI Evolution",   "emoji": "🎨", "output": "frontend/src/"},
    "12": {"name": "Performance",    "emoji": "⚙️", "output": "tests/"},
    "13": {"name": "Adsense Web",    "emoji": "🧩", "output": "frontend/"},
    "14": {"name": "Affiliate",      "emoji": "🔗", "output": "marketing/affiliates/"},
    "15": {"name": "Digital Prod",   "emoji": "📦", "output": "marketing/digital-products/"},
    "16": {"name": "Sponsorship",    "emoji": "🤝", "output": "marketing/sponsorships/"},
    "17": {"name": "Newsletter",     "emoji": "✉️", "output": "marketing/newsletter/"},
    "18": {"name": "Shorts",         "emoji": "🎞️", "output": "output/"},
    "19": {"name": "Distribution",   "emoji": "🚚", "output": "marketing/distribution/"},
    "20": {"name": "System Seller",  "emoji": "🛒", "output": "marketing/system-seller/"},
    "21": {"name": "Community",      "emoji": "💬", "output": "marketing/community/"},
    "22": {"name": "AB Testing",     "emoji": "🧪", "output": "marketing/abtesting/"},
    "23": {"name": "Virality",       "emoji": "🔥", "output": "research/virality/"},
    "24": {"name": "Net Forager",    "emoji": "🌐", "output": "research/improvements/"},
    "25": {"name": "Video Quality",  "emoji": "🎯", "output": "quality-reports/"},
}

def load_team_state():
    state_file = Path("logs/agents-state.json")
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text(encoding="utf-8-sig"))
    except:
        return {}

def load_history():
    history_file = Path("logs/agents-history.json")
    if not history_file.exists():
        return {"agents": {}, "cycles": []}
    try:
        return json.loads(history_file.read_text(encoding="utf-8-sig"))
    except:
        return {"agents": {}, "cycles": []}

def load_recent_events(limit=8):
    events_file = Path("logs/agents-events.jsonl")
    if not events_file.exists():
        return []
    rows = []
    try:
        for line in events_file.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except:
                continue
    except:
        return []
    return rows[-limit:]

def is_recent_iso(ts, max_age_seconds=120):
    if not ts or ts == "nunca":
        return False
    try:
        dt = datetime.fromisoformat(str(ts))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - dt.astimezone(timezone.utc)).total_seconds() <= max_age_seconds
    except:
        return False

def get_agent_status(num, info, team_state=None, history=None):
    memory_paths = list(Path(".").glob(f".copilot/agents/agent-{num}-*/memory.json"))
    last_run = None
    current_task = None
    running = False

    if memory_paths:
        try:
            mem = json.loads(memory_paths[0].read_text())
            last_run = mem.get("last_run")
            current_task = mem.get("current_task")
        except:
            pass

    # Prefer real telemetry from run_agents.ps1 state file
    if team_state and isinstance(team_state.get("agents"), list):
        try:
            agent = next((a for a in team_state["agents"] if str(a.get("agent_file", "")).startswith(f"{num}-")), None)
            if not agent:
                raise ValueError("agent_not_found")
            status = (agent.get("status") or "").lower()
            action = agent.get("action")
            finished = agent.get("finished_at")
            started = agent.get("started_at")
            running = status == "running"
            if action:
                current_task = action
            if finished:
                last_run = finished
            elif started:
                last_run = started
        except:
            pass
    else:
        # Fallback: per-agent PID files if telemetry is unavailable
        pid_file = Path(f"logs/agent-{num}.pid")
        if pid_file.exists():
            try:
                pid = int(pid_file.read_text(encoding="utf-8").strip().replace("\ufeff", ""))
                running = is_pid_running(pid)
            except:
                pass

    if (not last_run or last_run == "nunca") and isinstance(history, dict):
        last_hist = history.get("last_finished_at") or history.get("last_started_at")
        if last_hist:
            last_run = last_hist

    # Último archivo de output generado
    output_dir = Path(info["output"])
    latest_file = None
    latest_time = None
    if output_dir.exists():
        files = sorted(output_dir.glob("**/*"), key=lambda f: f.stat().st_mtime if f.is_file() else 0)
        if files:
            latest = [f for f in files if f.is_file()]
            if latest:
                latest_file = latest[-1].name
                ts = latest[-1].stat().st_mtime
                latest_time = datetime.fromtimestamp(ts).strftime("%H:%M %d/%m")

    return {
        "running": running,
        "last_run": last_run or "nunca",
        "current_task": current_task or ("trabajando..." if running else "en espera"),
        "recently_active": is_recent_iso(last_run),
        "latest_output": latest_file,
        "latest_time": latest_time,
        "runs": int((history or {}).get("runs", 0)),
        "done": int((history or {}).get("done", 0)),
        "errors": int((history or {}).get("errors", 0)),
    }

def get_master_status():
    pid_file = Path("logs/master.pid")
    if not pid_file.exists():
        return False, None, 0

    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip().replace("\ufeff", ""))
        if not is_pid_running(pid):
            return False, None, 0
        # Count log lines as proxy for current cycle progress
        today_log = Path(f"logs/master-{datetime.now().strftime('%Y-%m-%d')}.log")
        lines = 0
        if today_log.exists():
            lines = sum(1 for _ in today_log.open())
        return True, pid, lines
    except:
        return False, None, 0

def is_pid_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if os.name == "nt":
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except:
        return False

def get_pipeline_stats():
    q_file = Path("pipeline_queue.json")
    if not q_file.exists():
        return {}

    try:
        queue = json.loads(q_file.read_text())
        stats = {}
        for item in queue:
            s = item.get("status", "UNKNOWN")
            stats[s] = stats.get(s, 0) + 1
        return stats
    except:
        return {}

def get_latest_briefing_summary():
    files = sorted(Path("briefings").glob("*.md")) if Path("briefings").exists() else []
    if not files:
        return None, None

    latest = files[-1]
    lines = latest.read_text().split("\n")[:15]
    summary = "\n".join(lines)
    return latest.name, summary

def get_needs_from_human():
    needs_file = Path("NEEDS_FROM_HUMAN.md")
    if not needs_file.exists():
        return None

    try:
        content = needs_file.read_text(encoding="utf-8")
    except PermissionError:
        # Avoid crashing the monitor when another process is writing this file.
        return None
    blockers = [l.strip() for l in content.split("\n") if l.strip().startswith("- [ ] **")]
    return blockers[:3] if blockers else None

def render(clear_screen=True):
    if clear_screen:
        os.system("clear" if os.name != "nt" else "cls")

    team_state = load_team_state()
    history = load_history()
    recent_events = load_recent_events(limit=10)
    master_running, master_pid, log_lines = get_master_status()
    pipeline_stats = get_pipeline_stats()
    briefing_name, briefing_summary = get_latest_briefing_summary()
    needs = get_needs_from_human()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"╔{'═'*58}╗")
    print(f"║  VidFlow AI — Estado del Sistema       {now}  ║")
    print(f"╚{'═'*58}╝")
    print()

    # Master status
    if master_running:
        print(f"  🟢 SISTEMA ACTIVO  (PID {master_pid} · {log_lines} líneas de log hoy)")
        if os.name == "nt":
            print(f"     Para parar: Stop-Process -Id {master_pid}")
        else:
            print(f"     Para parar: kill {master_pid}")
    else:
        print("  🔴 SISTEMA PARADO")
        print("     Para arrancar:")
        if os.name == "nt":
            print("     powershell -ExecutionPolicy Bypass -File .\\start.ps1 --auto")
        else:
            print("     nohup bash scripts/run_agents.sh --loop > logs/master.log 2>&1 &")
    print()

    # Agent status table
    print("  ── AGENTES ────────────────────────────────────────────")
    print(f"  {'#':2}  {'Nombre':14} {'Estado':12} {'Runs':4} {'OK':3} {'ERR':3} {'Tarea actual'}")
    print(f"  {'─'*2}  {'─'*14} {'─'*12} {'─'*4} {'─'*3} {'─'*3} {'─'*24}")

    for num, info in AGENTS.items():
        agent_key = next((k for k in (history.get("agents") or {}).keys() if k.startswith(f"{num}-")), None)
        agent_hist = (history.get("agents") or {}).get(agent_key, {})
        status = get_agent_status(num, info, team_state=team_state, history=agent_hist)
        if status["running"]:
            state = "🟢 corriendo"
        elif master_running and status.get("recently_active"):
            state = "🟡 activo"
        else:
            state = "⚪ en espera"
        task = (status["current_task"] or "")[:24]
        print(f"  {num}   {info['emoji']} {info['name']:12} {state:12} {status['runs']:>4} {status['done']:>3} {status['errors']:>3} {task}")

    print()

    # Pipeline queue
    print("  ── COLA DE VÍDEOS ─────────────────────────────────────")
    if pipeline_stats:
        status_emoji = {
            "UPLOADED":       "✅",
            "APPROVED":       "🔵",
            "QUALITY_CHECK":  "🔍",
            "GENERATING":     "🟡",
            "FIX_REQUIRED":   "🔴",
            "CONTENT_REVISION":"🟠",
            "PENDING":        "⬜",
        }
        for s, count in sorted(pipeline_stats.items()):
            emoji = status_emoji.get(s, "❓")
            print(f"    {emoji}  {s}: {count}")
    else:
        print("    (cola vacía o pipeline_queue.json no encontrado)")

    print()

    # Needs from human
    if needs:
        print("  ── NECESITO TU AYUDA ──────────────────────────────────")
        for need in needs:
            print(f"    {need[:60]}")
        print(f"    Ver detalles en: NEEDS_FROM_HUMAN.md")
        print()

    # Latest briefing
    if briefing_name:
        print(f"  ── ÚLTIMO BRIEFING: {briefing_name} ───────────────")
        for line in (briefing_summary or "").split("\n")[:8]:
            if line.strip():
                print(f"    {line[:60]}")
        print()

    if recent_events:
        print("  ── ÚLTIMOS EVENTOS (reales) ───────────────────────────")
        for ev in recent_events[-8:]:
            ts = (ev.get("ts") or "")[11:19]
            ag = (ev.get("agent") or "system").replace(".agent.md", "")
            st = ev.get("status") or ""
            action = (ev.get("action") or "")[:38]
            print(f"    {ts}  {ag:24} {st:8} {action}")
        print()

    if MODE == "--watch":
        print(f"  Actualizando en 15s... (Ctrl+C para salir)")

    return {
        "master_running": master_running,
        "agents": {
            n: get_agent_status(
                n,
                i,
                team_state=team_state,
                history=(history.get("agents") or {}).get(
                    next((k for k in (history.get("agents") or {}).keys() if k.startswith(f"{n}-")), ""),
                    {},
                ),
            )
            for n, i in AGENTS.items()
        },
        "pipeline": pipeline_stats,
        "needs_human": needs,
        "recent_events": recent_events,
    }

if MODE == "--json":
    print(json.dumps(render(clear_screen=False), indent=2, default=str))
elif MODE == "--once":
    render()
else:
    try:
        while True:
            render()
            time.sleep(15)
    except KeyboardInterrupt:
        print("\n  Monitor parado.")
