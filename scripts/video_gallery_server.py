#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"
REMOTION_OUT = ROOT / "remotion" / "out"
REPORTS = ROOT / "logs" / "agent-reports"
LEARNING = ROOT / "logs" / "agent-learning"
HISTORY = ROOT / "logs" / "agents-history.json"
INCOME = ROOT / "monetization" / "income_tracker.json"
NEEDS = ROOT / "NEEDS_FROM_HUMAN.md"

app = FastAPI(title="VidFlow Operations Center")
app.mount("/media-output", StaticFiles(directory=str(OUTPUT)), name="media_output")
if REMOTION_OUT.exists():
    app.mount("/media-remotion", StaticFiles(directory=str(REMOTION_OUT)), name="media_remotion")
if REPORTS.exists():
    app.mount("/files-reports", StaticFiles(directory=str(REPORTS)), name="files_reports")
if LEARNING.exists():
    app.mount("/files-learning", StaticFiles(directory=str(LEARNING)), name="files_learning")


def _list_videos() -> list[tuple[str, str, float]]:
    items: list[tuple[str, str, float]] = []
    if OUTPUT.exists():
        for p in OUTPUT.rglob("*.mp4"):
            rel = p.relative_to(OUTPUT).as_posix()
            items.append((str(p), f"/media-output/{rel}", p.stat().st_mtime))
    if REMOTION_OUT.exists():
        for p in REMOTION_OUT.rglob("*.mp4"):
            rel = p.relative_to(REMOTION_OUT).as_posix()
            items.append((str(p), f"/media-remotion/{rel}", p.stat().st_mtime))
    items.sort(key=lambda x: x[2], reverse=True)
    return items


def _list_files(path: Path, prefix: str) -> list[tuple[str, str, float]]:
    if not path.exists():
        return []
    items = []
    for p in sorted(path.glob("*.md")):
        items.append((p.name, f"{prefix}/{p.name}", p.stat().st_mtime))
    items.sort(key=lambda x: x[2], reverse=True)
    return items


def _income_total() -> float:
    if not INCOME.exists():
        return 0.0
    try:
        data = json.loads(INCOME.read_text(encoding="utf-8-sig"))
        if not isinstance(data, list):
            return 0.0
        return float(sum(float(x.get("estimated_monthly", 0) or 0) for x in data))
    except Exception:
        return 0.0


def _pending_needs() -> int:
    if not NEEDS.exists():
        return 0
    return sum(1 for ln in NEEDS.read_text(encoding="utf-8-sig", errors="ignore").splitlines() if ln.strip().startswith("- [ ]"))


def _latest_advances() -> list[tuple[str, str, str]]:
    if not HISTORY.exists():
        return []
    try:
        h = json.loads(HISTORY.read_text(encoding="utf-8-sig"))
    except Exception:
        return []
    out: list[tuple[str, str, str]] = []
    for agent_file, d in (h.get("agents") or {}).items():
        out.append((agent_file.replace(".agent.md", ""), str(d.get("last_status", "")), str(d.get("last_action", ""))))
    out.sort(key=lambda x: x[0])
    return out


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    videos = _list_videos()
    reports = _list_files(REPORTS, "/files-reports")
    learning = _list_files(LEARNING, "/files-learning")
    income_total = _income_total()
    needs_pending = _pending_needs()
    advances = _latest_advances()

    video_cards = []
    for full, url, mtime in videos:
        name = Path(full).name
        folder = str(Path(full).parent.relative_to(ROOT)).replace("\\", "/")
        t = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        video_cards.append(
            f"""
            <div class="card">
              <video controls preload="metadata" src="{url}"></video>
              <div class="meta"><b>{name}</b></div>
              <div class="meta">{folder}</div>
              <div class="meta">{t}</div>
              <a href="{url}" target="_blank">Abrir archivo</a>
            </div>
            """
        )

    report_cards = []
    for name, url, mtime in reports[:40]:
        t = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        report_cards.append(f'<div class="list-item"><a href="{url}" target="_blank">{name}</a><span>{t}</span></div>')

    learning_cards = []
    for name, url, mtime in learning[:40]:
        t = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        learning_cards.append(f'<div class="list-item"><a href="{url}" target="_blank">{name}</a><span>{t}</span></div>')

    advances_rows = []
    for ag, st, act in advances:
        advances_rows.append(f"<tr><td>{ag}</td><td>{st}</td><td>{act}</td></tr>")

    return f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>VidFlow Ops Center</title>
  <style>
    body {{ background:#0f172a; color:#e2e8f0; font-family:Arial,sans-serif; margin:0; }}
    .wrap {{ max-width:1300px; margin:24px auto; padding:0 16px; }}
    h1 {{ margin:0 0 8px; }}
    .sub {{ opacity:.8; margin-bottom:14px; }}
    .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:12px; margin-bottom:16px; }}
    .stat {{ background:#111827; border:1px solid #334155; border-radius:10px; padding:12px; }}
    .k {{ font-size:28px; font-weight:800; color:#38bdf8; }}
    .tabs {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:16px; }}
    .tab {{ background:#1e293b; color:#e2e8f0; border:1px solid #334155; border-radius:8px; padding:6px 10px; cursor:pointer; }}
    .tab.active {{ background:#0ea5e9; color:#0b1120; border-color:#0ea5e9; font-weight:700; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(320px,1fr)); gap:16px; }}
    .card {{ background:#111827; border:1px solid #334155; border-radius:10px; padding:10px; }}
    video {{ width:100%; border-radius:8px; background:#000; }}
    .meta {{ font-size:12px; opacity:.9; margin-top:6px; word-break:break-all; }}
    a {{ color:#38bdf8; font-size:13px; }}
    .list {{ background:#111827; border:1px solid #334155; border-radius:10px; padding:12px; }}
    .list-item {{ display:flex; justify-content:space-between; gap:8px; padding:6px 0; border-bottom:1px solid #1f2937; }}
    .list-item:last-child {{ border-bottom:none; }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; }}
    th, td {{ border-bottom:1px solid #334155; padding:7px; text-align:left; vertical-align:top; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>VidFlow Operations Center</h1>
    <div class="sub">localhost:3000 · videos + avances + ingresos + reportes + aprendizaje</div>

    <div class="stats">
      <div class="stat"><div>Videos actuales</div><div class="k">{len(videos)}</div></div>
      <div class="stat"><div>Reportes agentes</div><div class="k">{len(reports)}</div></div>
      <div class="stat"><div>Learning files</div><div class="k">{len(learning)}</div></div>
      <div class="stat"><div>Ingresos estimados/mes</div><div class="k">${income_total:.2f}</div></div>
      <div class="stat"><div>Needs pendientes</div><div class="k">{needs_pending}</div></div>
    </div>

    <div class="tabs">
      <button class="tab active" data-tab="videos" onclick="showTab('videos')">Videos</button>
      <button class="tab" data-tab="reports" onclick="showTab('reports')">Reportes</button>
      <button class="tab" data-tab="learning" onclick="showTab('learning')">Aprendizaje</button>
      <button class="tab" data-tab="advances" onclick="showTab('advances')">Avances agentes</button>
    </div>

    <section class="tab-content" id="tab-videos" style="display:block">
      <div class="grid">{''.join(video_cards) if video_cards else '<p>No hay videos todavía.</p>'}</div>
    </section>
    <section class="tab-content" id="tab-reports" style="display:none">
      <div class="list">{''.join(report_cards) if report_cards else '<p>Sin reportes.</p>'}</div>
    </section>
    <section class="tab-content" id="tab-learning" style="display:none">
      <div class="list">{''.join(learning_cards) if learning_cards else '<p>Sin aprendizaje registrado.</p>'}</div>
    </section>
    <section class="tab-content" id="tab-advances" style="display:none">
      <div class="list">
        <table>
          <thead><tr><th>Agente</th><th>Estado</th><th>Última acción</th></tr></thead>
          <tbody>{''.join(advances_rows) if advances_rows else '<tr><td colspan="3">Sin datos.</td></tr>'}</tbody>
        </table>
      </div>
    </section>
  </div>
  <script>
    function showTab(name) {{
      document.querySelectorAll('.tab').forEach(b => b.classList.toggle('active', b.dataset.tab === name));
      document.querySelectorAll('.tab-content').forEach(s => s.style.display = (s.id === 'tab-' + name) ? 'block' : 'none');
    }}
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000, reload=False)

