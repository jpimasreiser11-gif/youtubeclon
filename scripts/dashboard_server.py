#!/usr/bin/env python3
"""
dashboard_server.py — Servidor del Pixel Dashboard web

Uso:
  python scripts/dashboard_server.py          → puerto 7700
  python scripts/dashboard_server.py --port 8080

Abre en el navegador: http://localhost:7700
"""

import os, sys, json, glob, ctypes
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--port" else 7700

AGENT_NUMS = [f"{i:02d}" for i in range(0, 26)]

def _is_pid_running(pid):
    try:
        pid = int(pid)
    except:
        return False
    if pid <= 0:
        return False
    if os.name == "nt":
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except:
        return False

def _load_team_state():
    p = Path("logs/agents-state.json")
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except:
        return {}

def get_agent_state(num):
    state = {"status": "idle", "task": "", "last_run": "nunca"}
    team = _load_team_state()
    if isinstance(team.get("agents"), list):
        try:
            a = next((x for x in team["agents"] if str(x.get("agent_file", "")).startswith(f"{num}-")), None)
            if not a:
                raise ValueError("agent_not_found")
            st = (a.get("status") or "idle").lower()
            state["status"] = "working" if st == "running" else st
            state["task"] = a.get("action", "")
            state["last_run"] = a.get("finished_at") or a.get("started_at") or "nunca"
            return state
        except:
            pass

    for pattern in [f".copilot/agents/agent-{num}-*/memory.json",
                    f"agents-system/agent-{num}-*/memory.json"]:
        files = glob.glob(pattern)
        if files:
            try:
                mem = json.loads(Path(files[0]).read_text())
                state["last_run"] = mem.get("last_run", "nunca")
                state["task"] = mem.get("current_task", "")
                if mem.get("running"):
                    state["status"] = "working"
            except:
                pass
            break

    pid_file = Path(f"logs/agent-{num}.pid")
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            if _is_pid_running(pid):
                state["status"] = "working"
        except:
            pass
    return state

def get_master_status():
    pid_file = Path("logs/master.pid")
    if not pid_file.exists():
        return False, None
    try:
        pid = int(pid_file.read_text(encoding="utf-8").strip().replace("\ufeff", ""))
        return _is_pid_running(pid), pid if _is_pid_running(pid) else None
    except:
        return False, None

def get_queue_stats():
    stats = {}
    try:
        q = json.loads(Path("pipeline_queue.json").read_text())
        for item in q:
            s = item.get("status", "PENDING")
            stats[s] = stats.get(s, 0) + 1
    except:
        pass
    return stats

def get_changelog(n=50):
    progress_file = Path("logs/agent-progress/all-agents.progress.jsonl")
    if not progress_file.exists():
        return []
    rows = []
    try:
        for line in progress_file.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                rows.append({
                    "time": (ev.get("ts", "")[11:19]),
                    "date": (ev.get("ts", "")[:10]),
                    "agent": (ev.get("agent") or "system").replace(".agent.md", ""),
                    "type": "feat" if ev.get("status") == "done" else ("alert" if ev.get("status") == "error" else "info"),
                    "description": ev.get("action") or ev.get("type") or "",
                    "status": ev.get("status"),
                })
            except:
                continue
    except:
        return []
    return rows[-n:]

class DashHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Silenciar logs del servidor

    def send_json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            html_file = Path("scripts/web_dashboard.html")
            if html_file.exists():
                body = html_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", len(body))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_error(404, "web_dashboard.html not found")

        elif self.path == "/api/status":
            running, pid = get_master_status()
            agents = {num: get_agent_state(num) for num in AGENT_NUMS}
            self.send_json({
                "master_running": running,
                "master_pid": pid,
                "agents": agents,
                "timestamp": datetime.now().isoformat(),
            })

        elif self.path == "/api/changelog":
            self.send_json(get_changelog())

        elif self.path == "/api/queue":
            self.send_json(get_queue_stats())

        elif self.path == "/api/needs":
            needs = []
            needs_file = Path("NEEDS_FROM_HUMAN.md")
            if needs_file.exists():
                for line in needs_file.read_text().split("\n"):
                    if line.strip().startswith("- [ ]"):
                        needs.append(line.strip()[5:].strip())
            self.send_json(needs)

        else:
            self.send_error(404)

def main():
    os.chdir(Path(__file__).parent.parent)  # Run from project root
    print("\n======================================")
    print(" VidFlow AI - Pixel Dashboard")
    print(f" http://localhost:{PORT}")
    print(" Ctrl+C para parar")
    print("======================================\n")

    server = HTTPServer(("0.0.0.0", PORT), DashHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado.")

if __name__ == "__main__":
    main()
