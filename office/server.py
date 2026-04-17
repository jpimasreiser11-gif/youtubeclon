#!/usr/bin/env python3
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "logs"
OFFICE_HTML = ROOT / "office" / "index.html"

app = FastAPI(title="VidFlow Office API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return default


def _agent_name_from_file(agent_file: str) -> str:
    base = agent_file.replace(".agent.md", "")
    if "-" in base:
        return base.split("-", 1)[1]
    return base


def _find_inbox(agent_id: str) -> Path | None:
    candidates = []
    candidates.extend((ROOT / ".copilot" / "agents").glob(f"agent-{agent_id}-*/inbox"))
    candidates.extend((ROOT / "agents-system").glob(f"agent-{agent_id}-*/inbox"))
    candidates.extend((ROOT / ".github" / "agents").glob(f"{agent_id}-*/inbox"))
    for c in candidates:
        c.mkdir(parents=True, exist_ok=True)
        return c
    return None


def _agent_report_path(agent_id: str) -> Path | None:
    report_dir = LOGS / "agent-reports"
    if not report_dir.exists():
        return None
    matches = sorted(report_dir.glob(f"{agent_id}-*.md"))
    return matches[0] if matches else None


def _tail_jsonl(path: Path, max_lines: int = 500) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not path.exists():
        return out
    lines = path.read_text(encoding="utf-8-sig", errors="ignore").splitlines()[-max_lines:]
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _extract_files(action: str, result: str) -> list[dict[str, str]]:
    text = f"{action} {result}".strip()
    files: list[dict[str, str]] = []
    path_matches = re.findall(r"([A-Za-z0-9_\-./\\]+\.[A-Za-z0-9]{2,6})", text)
    seen = set()
    for p in path_matches:
        clean = p.strip(".,;:()[]{}")
        if clean in seen:
            continue
        seen.add(clean)
        op = "edit"
        low = action.lower()
        if "create" in low or "bootstrap" in low:
            op = "create"
        elif "fix" in low or "error" in low:
            op = "fix"
        elif "scan" in low or "research" in low:
            op = "research"
        files.append({"path": clean, "action": op})
    return files


def _extract_agent_id_from_need(text: str) -> str | None:
    m = re.search(r"agent[-\s]?(\d{2})", text, flags=re.IGNORECASE)
    if not m:
        return None
    return m.group(1)


@app.get("/")
def root():
    return FileResponse(str(OFFICE_HTML))


@app.get("/api/status")
def api_status():
    master_running = False
    master_pid = None
    pid_file = LOGS / "master.pid"
    if pid_file.exists():
        try:
            master_pid = int(pid_file.read_text(encoding="utf-8").strip().replace("\ufeff", ""))
            master_running = True
        except Exception:
            master_running = False
            master_pid = None

    state = _read_json(LOGS / "agents-state.json", {})
    agents_out: dict[str, Any] = {}
    for a in state.get("agents", []) if isinstance(state.get("agents"), list) else []:
        af = str(a.get("agent_file", ""))
        agent_id = af[:2] if len(af) >= 2 and af[:2].isdigit() else ""
        if not agent_id:
            continue
        st = str(a.get("status", "idle")).lower()
        status = "working" if st == "running" else st
        agents_out[agent_id] = {
            "name": _agent_name_from_file(af),
            "status": status,
            "task": a.get("action", ""),
            "last_run": a.get("finished_at") or a.get("started_at") or "nunca",
        }

    return {
        "master_running": master_running,
        "master_pid": master_pid,
        "agents": agents_out,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/changelog")
def api_changelog():
    events = []
    f = LOGS / "agents-events.jsonl"
    if f.exists():
        for line in f.read_text(encoding="utf-8-sig").splitlines()[-80:]:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
                events.append(
                    {
                        "time": (ev.get("ts", "")[11:16]),
                        "agent": (ev.get("agent") or "system").replace(".agent.md", ""),
                        "type": "feat" if ev.get("status") == "done" else ("alert" if ev.get("status") == "error" else "info"),
                        "description": ev.get("action") or ev.get("type") or "",
                    }
                )
            except Exception:
                continue
    return events[-50:]


@app.get("/api/queue")
def api_queue():
    q = _read_json(ROOT / "pipeline_queue.json", [])
    stats: dict[str, int] = {}
    if isinstance(q, list):
        for item in q:
            status = str((item or {}).get("status", "PENDING"))
            stats[status] = stats.get(status, 0) + 1
    return stats


@app.get("/api/needs")
def api_needs():
    needs_path = ROOT / "NEEDS_FROM_HUMAN.md"
    out = []
    if needs_path.exists():
        for ln in needs_path.read_text(encoding="utf-8-sig").splitlines():
            if ln.strip().startswith("- [ ]"):
                out.append(ln.strip()[5:].strip())
    return out


@app.get("/api/agent/{agent_id}")
def api_agent(agent_id: str):
    aid = agent_id.strip().zfill(2)[:2]
    report_path = _agent_report_path(aid)
    report_text = report_path.read_text(encoding="utf-8-sig", errors="ignore") if report_path else ""

    diary = "Sin diario disponible todavía."
    summary_lines: list[str] = []
    for ln in report_text.splitlines():
        s = ln.strip()
        if s.startswith("- Ultima accion:") or s.startswith("- Ultimo resultado:") or s.startswith("- Estado actual:"):
            summary_lines.append(s[2:].strip())
    if summary_lines:
        diary = " ".join(summary_lines)

    if aid == "00":
        dpath = ROOT / "diary" / "patriarch-diary.md"
        if dpath.exists():
            lines = [x.strip() for x in dpath.read_text(encoding="utf-8-sig", errors="ignore").splitlines() if x.strip()]
            if lines:
                diary = lines[-1]

    events = _tail_jsonl(LOGS / "agents-events.jsonl", max_lines=1200)
    agent_events = []
    key = f"{aid}-"
    for ev in events:
        ag = str(ev.get("agent", ""))
        if ag.startswith(key):
            agent_events.append(ev)
    agent_events = agent_events[-20:]

    log = [
        {
            "time": str(ev.get("ts", ""))[11:16] or "--:--",
            "status": str(ev.get("status", "")),
            "action": str(ev.get("action", "")),
            "result": str(ev.get("result", "")),
        }
        for ev in agent_events
    ]

    files: list[dict[str, str]] = []
    for ev in reversed(agent_events):
        files.extend(_extract_files(str(ev.get("action", "")), str(ev.get("result", ""))))
        if len(files) >= 12:
            break

    return {"agent_id": aid, "diary": diary, "files": files[:12], "log": log}


class NeedReply(BaseModel):
    index: int
    reply: str


@app.post("/api/needs/reply")
def api_needs_reply(body: NeedReply):
    needs_path = ROOT / "NEEDS_FROM_HUMAN.md"
    replies = ROOT / "NEEDS_FROM_HUMAN_REPLIES.md"
    if not needs_path.exists():
        return {"ok": False, "error": "needs_file_not_found"}

    lines = needs_path.read_text(encoding="utf-8-sig", errors="ignore").splitlines()
    pending: list[tuple[int, str]] = []
    for idx, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("- [ ]"):
            pending.append((idx, s[5:].strip()))

    if body.index < 0 or body.index >= len(pending):
        return {"ok": False, "error": "invalid_need_index"}

    line_idx, need_text = pending[body.index]
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines[line_idx] = f"- [x] {need_text} (Respondido {stamp})"
    needs_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    agent_id = _extract_agent_id_from_need(need_text) or "24"
    inbox = _find_inbox(agent_id)
    inbox_file = None
    if inbox is not None:
        ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        inbox_file = inbox / f"human-need-reply-{ts}.md"
        content = (
            "FROM: Humano\n"
            f"TO: Agent-{agent_id}\n"
            f"TIME: {datetime.now().strftime('%H:%M')}\n\n"
            "RESPUESTA A NEED:\n"
            f"{need_text}\n\n"
            "RESPUESTA HUMANA:\n"
            f"{body.reply}\n"
        )
        inbox_file.write_text(content, encoding="utf-8")

    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    block = (
        f"- [{stamp}] Need #{body.index} ({need_text})\n"
        f"  - Reply: {body.reply}\n"
        f"  - Notified: Agent-{agent_id}\n"
    )
    with replies.open("a", encoding="utf-8") as f:
        f.write(block)
    return {
        "ok": True,
        "need": need_text,
        "agent_notified": agent_id,
        "saved_to": str(inbox_file.relative_to(ROOT)) if inbox_file else None,
    }


class ChatMsg(BaseModel):
    agent_id: str
    message: str
    from_human: str = "Humano"


@app.post("/api/chat")
def api_chat(body: ChatMsg):
    aid = body.agent_id.strip().zfill(2)[:2]
    inbox = _find_inbox(aid)
    if inbox is None:
        return {"ok": False, "error": "inbox_not_found"}
    ts = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    msg_path = inbox / f"human-{ts}.md"
    content = (
        f"FROM: {body.from_human}\n"
        f"TO: Agent-{aid}\n"
        f"TIME: {datetime.now().strftime('%H:%M')}\n\n"
        f"{body.message}\n"
    )
    msg_path.write_text(content, encoding="utf-8")
    return {"ok": True, "saved_to": str(msg_path.relative_to(ROOT))}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7700, reload=False)
