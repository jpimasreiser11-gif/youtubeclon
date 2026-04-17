#!/usr/bin/env python3
"""
pixel_dashboard.py — VidFlow AI · Pixel Office
Muestra los 11 agentes como muñequitos animados en la terminal.

Uso:
  python scripts/pixel_dashboard.py          # pantalla completa
  python scripts/pixel_dashboard.py --mini   # versión compacta
  python scripts/pixel_dashboard.py --log    # + panel de logs
"""

import os, sys, json, time, math, glob, random, ctypes
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.columns import Columns
from rich.rule import Rule
from rich import box

# ── SPRITES (pixel art con bloques Unicode) ──────────────────────────
# Cada sprite tiene: idle / working / done / error (4 frames de animación)

SPRITES = {
    "researcher": {
        "color": "cyan",
        "idle":    ["  🔍  ", " (•‿•) ", " /||\\ ", "  /\\  "],
        "working": ["  🔍  ", " (•ᴗ•) ", " \\||/ ", "  /\\  "],
        "done":    ["  ✅  ", " (^‿^) ", " /||\\ ", "  /\\  "],
        "error":   ["  ❌  ", " (×﹏×) ", " /||\\ ", "  /\\  "],
    },
    "content": {
        "color": "magenta",
        "idle":    ["  ✍️   ", " (o‿o) ", " /||\\ ", "  /\\  "],
        "working": ["  ✍️   ", " (o_o) ", " \\|=/ ", "  /\\  "],
        "done":    ["  📄  ", " (^‿^) ", " /||\\ ", "  /\\  "],
        "error":   ["  📄  ", " (×_×) ", " /||\\ ", "  /\\  "],
    },
    "code": {
        "color": "green",
        "idle":    ["  💻  ", " (·_·) ", " /||\\ ", "  /\\  "],
        "working": ["  💻  ", " (-_-) ", " \\|>/ ", "  /\\  "],
        "done":    ["  ✅  ", " (^_^) ", " /||\\ ", "  /\\  "],
        "error":   ["  🐛  ", " (o_O) ", " /||\\ ", "  /\\  "],
    },
    "seo": {
        "color": "yellow",
        "idle":    ["  📈  ", " (·‿·) ", " /||\\ ", "  /\\  "],
        "working": ["  📈  ", " (·ᴗ·) ", " /=|\\ ", "  /\\  "],
        "done":    ["  🏆  ", " (^‿^) ", " /||\\ ", "  /\\  "],
        "error":   ["  📉  ", " (×‿×) ", " /||\\ ", "  /\\  "],
    },
    "quality": {
        "color": "blue",
        "idle":    ["  🛡️   ", " (O‿O) ", " /||\\ ", "  /\\  "],
        "working": ["  🛡️   ", " (O_O) ", " \\||/ ", "  /\\  "],
        "done":    ["  ✅  ", " (^O^) ", " /||\\ ", "  /\\  "],
        "error":   ["  ⚠️   ", " (×O×) ", " /||\\ ", "  /\\  "],
    },
    "money": {
        "color": "gold1",
        "idle":    ["  💰  ", " ($‿$) ", " /||\\ ", "  /\\  "],
        "working": ["  💰  ", " ($ᴗ$) ", " /=|\\ ", "  /\\  "],
        "done":    ["  💎  ", " (^$^) ", " /||\\ ", "  /\\  "],
        "error":   ["  💸  ", " ($×$) ", " /||\\ ", "  /\\  "],
    },
    "analytics": {
        "color": "orchid",
        "idle":    ["  📊  ", " (·_·) ", " /||\\ ", "  /\\  "],
        "working": ["  📊  ", " (·‿·) ", " \\|~/ ", "  /\\  "],
        "done":    ["  📋  ", " (^_^) ", " /||\\ ", "  /\\  "],
        "error":   ["  ⚠️   ", " (×_×) ", " /||\\ ", "  /\\  "],
    },
    "fixer": {
        "color": "orange_red1",
        "idle":    ["  🔧  ", " (·‿·) ", " /||\\ ", "  /\\  "],
        "working": ["  🔧  ", " (·_·) ", " \\||/ ", "  /\\  "],
        "done":    ["  ✅  ", " (^‿^) ", " /||\\ ", "  /\\  "],
        "error":   ["  🔥  ", " (O_O) ", " /||\\ ", "  /\\  "],
    },
    "trends": {
        "color": "deep_sky_blue1",
        "idle":    ["  🌊  ", " (∘‿∘) ", " /||\\ ", "  /\\  "],
        "working": ["  🌊  ", " (∘ᴗ∘) ", " \\||/ ", "  /\\  "],
        "done":    ["  🎯  ", " (^∘^) ", " /||\\ ", "  /\\  "],
        "error":   ["  ⚡  ", " (×∘×) ", " /||\\ ", "  /\\  "],
    },
    "scheduler": {
        "color": "white",
        "idle":    ["  🗓️   ", " (•‿•) ", " /||\\ ", "  /\\  "],
        "working": ["  🗓️   ", " (•_•) ", " \\|~/ ", "  /\\  "],
        "done":    ["  📬  ", " (^‿^) ", " /||\\ ", "  /\\  "],
        "error":   ["  🚨  ", " (•O•) ", " /||\\ ", "  /\\  "],
    },
    "videoresearcher": {
        "color": "red",
        "idle":    ["  🎬  ", " (≖‿≖) ", " /||\\ ", "  /\\  "],
        "working": ["  🎬  ", " (≖_≖) ", " \\|🔎/ ", "  /\\  "],
        "done":    ["  🚀  ", " (^≖^) ", " /||\\ ", "  /\\  "],
        "error":   ["  📡  ", " (≖×≖) ", " /||\\ ", "  /\\  "],
    },
}

AGENT_CONFIG = [
    {"num": "01", "name": "Researcher",    "short": "researcher",      "role": "Investiga competencia y oportunidades"},
    {"num": "02", "name": "ContentForge",  "short": "content",         "role": "Genera guiones para 6 canales"},
    {"num": "03", "name": "CodeSentinel",  "short": "code",            "role": "Revisa y mejora el código"},
    {"num": "04", "name": "SEO Engineer",  "short": "seo",             "role": "Optimiza títulos y descripciones"},
    {"num": "05", "name": "QualityGate",   "short": "quality",         "role": "Valida vídeos antes de subir"},
    {"num": "06", "name": "MoneyFinder",   "short": "money",           "role": "Busca oportunidades de ingresos"},
    {"num": "07", "name": "DataAnalyst",   "short": "analytics",       "role": "Lee métricas y genera insights"},
    {"num": "08", "name": "Fixer",         "short": "fixer",           "role": "Arregla errores del pipeline"},
    {"num": "09", "name": "TrendHunter",   "short": "trends",          "role": "Detecta trending topics"},
    {"num": "10", "name": "Scheduler",     "short": "scheduler",       "role": "Orquesta todos los agentes"},
    {"num": "11", "name": "UIEvolution",   "short": "uievolution",     "role": "Mejora UI/UX del sistema"},
    {"num": "12", "name": "Performance",   "short": "performance",     "role": "Optimiza rendimiento"},
    {"num": "13", "name": "AdsenseWeb",    "short": "adsenseweb",      "role": "Monetiza web con ads"},
    {"num": "14", "name": "Affiliate",     "short": "affiliate",       "role": "Estrategia de afiliados"},
    {"num": "15", "name": "DigitalProd",   "short": "digitalprod",     "role": "Productos digitales"},
    {"num": "16", "name": "Sponsorship",   "short": "sponsorship",     "role": "Patrocinios"},
    {"num": "17", "name": "Newsletter",    "short": "newsletter",      "role": "Crecimiento newsletter"},
    {"num": "18", "name": "Shorts",        "short": "shorts",          "role": "Pipeline de Shorts"},
    {"num": "19", "name": "Distribution",  "short": "distribution",    "role": "Distribución multicanal"},
    {"num": "20", "name": "SystemSeller",  "short": "systemseller",    "role": "Venta de sistema"},
    {"num": "21", "name": "Community",     "short": "community",       "role": "Comunidad"},
    {"num": "22", "name": "ABTesting",     "short": "abtesting",       "role": "A/B testing"},
    {"num": "23", "name": "Virality",      "short": "virality",        "role": "Optimización viral"},
]

TASK_PHRASES = {
    "researcher":     ["Analizando competidores...", "Buscando afiliados...", "Revisando algoritmo YT...", "Comparando RPMs..."],
    "content":        ["Escribiendo hook...", "Generando guión ES...", "Script Mind Warp...", "TikTok Mentes Rotas..."],
    "code":           ["Revisando pipeline.py...", "Optimizando ffmpeg...", "Añadiendo try/except...", "Tests del uploader..."],
    "seo":            ["Analizando keywords...", "Optimizando títulos...", "Generando tags...", "A/B test thumbnails..."],
    "quality":        ["Check duración...", "Verificando audio...", "Revisando subtítulos...", "Anti-ban scan..."],
    "money":          ["Buscando afiliados...", "Trackeando CPAs...", "Pipeline patrocinios...", "Comparando programas..."],
    "analytics":      ["Leyendo métricas...", "Calculando RPM...", "Scorecard canales...", "Comparando semanas..."],
    "fixer":          ["Monitorizando logs...", "Fix pantalla negra...", "Refreshing OAuth...", "Rate limit backoff..."],
    "trends":         ["Google Trends scan...", "Reddit r/ChatGPT...", "Buscando virales...", "Scoring tendencias..."],
    "scheduler":      ["Coordinando agentes...", "Generando briefing...", "Revisando queue...", "Planificando mañana..."],
    "videoresearcher":["Buscando técnicas...", "Analizando retención...", "Estudiando Veo 3.1...", "Probando hooks..."],
}

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

def read_agent_state(num):
    """Lee el estado real del agente desde sus archivos"""
    state = {"status": "idle", "task": "", "last_run": "nunca", "files_changed": 0}
    team = _load_team_state()
    if isinstance(team.get("agents"), list):
        try:
            idx = int(num) - 1
            a = team["agents"][idx]
            st = (a.get("status") or "idle").lower()
            state["status"] = "working" if st == "running" else st
            state["task"] = a.get("action") or ""
            state["last_run"] = a.get("finished_at") or a.get("started_at") or "nunca"
        except:
            pass

    # Leer memory.json
    patterns = [
        f".copilot/agents/agent-{num}-*/memory.json",
        f"agents-system/agent-{num}-*/memory.json",
    ]
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            try:
                mem = json.loads(Path(files[0]).read_text())
                state["last_run"] = mem.get("last_run", "nunca")
                state["task"] = mem.get("current_task", "")
                state["status"] = "working" if mem.get("running") else "idle"
            except:
                pass
            break

    # Detectar si está corriendo (PID)
    pid_file = Path(f"logs/agent-{num}.pid")
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            if _is_pid_running(pid):
                state["status"] = "working"
        except:
            pass

    # Contar archivos cambiados hoy
    today = datetime.now().strftime("%Y-%m-%d")
    changed = 0
    for f in Path(".").rglob("*.py"):
        try:
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")
            if mtime == today:
                changed += 1
        except:
            pass
    state["files_changed"] = changed

    return state

def read_pipeline_queue():
    stats = {"UPLOADED": 0, "APPROVED": 0, "GENERATING": 0,
             "FIX_REQUIRED": 0, "QUALITY_CHECK": 0, "PENDING": 0}
    try:
        q = json.loads(Path("pipeline_queue.json").read_text())
        for item in q:
            s = item.get("status", "PENDING")
            stats[s] = stats.get(s, 0) + 1
    except:
        pass
    return stats

def read_recent_changes(n=8):
    changes = []
    changelog = Path("logs/changelog.md")
    if changelog.exists():
        lines = changelog.read_text().split("\n")
        for line in reversed(lines):
            if line.strip() and not line.startswith("#"):
                changes.append(line.strip())
                if len(changes) >= n:
                    break
    else:
        # Fallback: leer últimas líneas del log maestro
        logs = sorted(Path("logs").glob("master-*.log")) if Path("logs").exists() else []
        if logs:
            try:
                lines = logs[-1].read_text().split("\n")
                for line in reversed(lines):
                    if line.strip() and ("✓" in line or "✅" in line or "Fixed" in line):
                        changes.append(line.strip()[-70:])
                        if len(changes) >= n:
                            break
            except:
                pass
    return changes or ["Sin cambios registrados todavía"]

def read_master_status():
    running = False
    pid = None
    if Path("logs/master.pid").exists():
        try:
            pid = int(Path("logs/master.pid").read_text(encoding="utf-8").strip().replace("\ufeff", ""))
            running = _is_pid_running(pid)
        except:
            pass
    return running, pid

def build_agent_card(agent, frame, t):
    """Construye la tarjeta visual de un agente"""
    num = agent["num"]
    short = agent["short"]
    name = agent["name"]
    sprite_set = SPRITES.get(short, SPRITES["scheduler"])
    color = sprite_set["color"]

    # Leer estado real o simular
    state = read_agent_state(num)
    status = state["status"]

    # Animación: cicla entre frames según el tiempo
    anim_speed = 0.4 if status == "working" else 0.15
    frame_idx = int(t / anim_speed) % 4

    sprite_frames = sprite_set.get(status, sprite_set["idle"])

    # Efecto bobbing: el muñeco sube y baja ligeramente cuando trabaja
    bob = ""
    if status == "working":
        bob_cycle = int(t / 0.5) % 2
        sprite_lines = list(sprite_frames)
        if bob_cycle == 1 and len(sprite_lines) >= 2:
            sprite_lines = ["      "] + sprite_lines[:-1]
    else:
        sprite_lines = list(sprite_frames)

    # Tarea actual (rotando si está trabajando)
    task_list = TASK_PHRASES.get(short, ["Trabajando..."])
    task_idx = int(t / 3) % len(task_list)
    current_task = state["task"] or task_list[task_idx]
    if len(current_task) > 22:
        current_task = current_task[:22] + "…"

    # Burbuja de estado
    status_icon = {"idle": "💤", "working": "⚡", "done": "✅", "error": "🔴"}.get(status, "❓")

    # Construir texto del sprite
    sprite_text = Text()
    sprite_text.append(f"  {sprite_lines[0]}\n", style=f"bold {color}")
    sprite_text.append(f"  {sprite_lines[1]}\n", style=color)
    sprite_text.append(f"  {sprite_lines[2]}\n", style="white")
    sprite_text.append(f"  {sprite_lines[3]}\n", style="white")

    # Info debajo del sprite
    sprite_text.append(f"\n  {status_icon} ", style="bold")
    if status == "working":
        sprite_text.append(current_task, style=f"bold {color}")
    elif status == "done":
        sprite_text.append("¡Completado!", style="bold green")
    elif status == "error":
        sprite_text.append("Error — fixer en camino", style="bold red")
    else:
        sprite_text.append(f"En espera", style="dim")

    sprite_text.append(f"\n  ⏱ {state['last_run'][-10:]}", style="dim")

    # Color del borde según estado
    border_style = {
        "working": f"bold {color}",
        "done":    "bold green",
        "error":   "bold red",
        "idle":    "dim",
    }.get(status, "dim")

    return Panel(
        sprite_text,
        title=f"[bold {color}]{num} · {name}[/]",
        border_style=border_style,
        width=24,
        height=12,
    )

def build_pipeline_panel(stats):
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column(width=14)
    t.add_column(width=6, justify="right")

    icons = {
        "UPLOADED":        ("✅ Subidos",    "green"),
        "APPROVED":        ("🔵 Aprobados", "blue"),
        "QUALITY_CHECK":   ("🔍 En check",  "cyan"),
        "GENERATING":      ("🟡 Generando", "yellow"),
        "FIX_REQUIRED":    ("🔴 Con error", "red"),
        "PENDING":         ("⬜ Pendiente", "dim"),
    }
    for key, (label, color) in icons.items():
        count = stats.get(key, 0)
        if count > 0:
            bar = "█" * min(count, 10)
            t.add_row(
                Text(label, style=color),
                Text(f"{count} {bar}", style=color),
            )
    return Panel(t, title="[bold]Cola de vídeos[/]", border_style="dim", height=10)

def build_changes_panel(changes):
    txt = Text()
    for i, change in enumerate(changes[:7]):
        clean = change.lstrip("- ").lstrip("[").strip()
        if "✓" in change or "✅" in change or "ok" in change.lower():
            txt.append(f"  ✅ {clean[:55]}\n", style="green")
        elif "error" in change.lower() or "❌" in change:
            txt.append(f"  ❌ {clean[:55]}\n", style="red")
        elif "fix" in change.lower() or "🔧" in change:
            txt.append(f"  🔧 {clean[:55]}\n", style="orange1")
        else:
            txt.append(f"  📝 {clean[:55]}\n", style="dim")
    if not changes or changes == ["Sin cambios registrados todavía"]:
        txt.append("  Sin cambios recientes.\n", style="dim")
        txt.append("  Los agentes escribirán aquí\n", style="dim")
        txt.append("  cuando empiecen a trabajar.", style="dim")
    return Panel(txt, title="[bold]Últimos cambios[/]", border_style="dim")

def build_status_bar(running, pid, t):
    now = datetime.now().strftime("%H:%M:%S")
    if running:
        pulse = "●" if int(t * 2) % 2 == 0 else "○"
        status = Text()
        status.append(f" {pulse} SISTEMA ACTIVO ", style="bold green on dark_green")
        status.append(f"  PID {pid}  ", style="dim")
        status.append(f"  {now}  ", style="bold white")
        status.append("  Para parar: bash start.sh --stop  ", style="dim")
    else:
        status = Text()
        status.append(" ● SISTEMA PARADO ", style="bold red on dark_red")
        status.append(f"  {now}  ", style="dim")
        status.append("  Para arrancar: bash start.sh --auto  ", style="dim yellow")
    return Panel(status, height=3, border_style="dim")

def render_frame(t):
    running, pid = read_master_status()
    pipeline_stats = read_pipeline_queue()
    changes = read_recent_changes()

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="agents", ratio=3),
        Layout(name="bottom", ratio=1),
    )
    layout["bottom"].split_row(
        Layout(name="pipeline", ratio=1),
        Layout(name="changes", ratio=2),
    )

    # Header
    layout["header"].update(build_status_bar(running, pid, t))

    # Agentes — distribución dinámica en filas de 6
    rows = [AGENT_CONFIG[i:i + 6] for i in range(0, len(AGENT_CONFIG), 6)]
    agents_layout = Layout()
    agents_layout.split_column(*[Layout(name=f"row{i}", size=12) for i in range(len(rows))])
    for i, row_agents in enumerate(rows):
        cards = [build_agent_card(a, 0, t) for a in row_agents]
        agents_layout[f"row{i}"].update(Columns(cards, equal=True, expand=True))
    layout["agents"].update(agents_layout)

    # Bottom
    layout["pipeline"].update(build_pipeline_panel(pipeline_stats))
    layout["changes"].update(build_changes_panel(changes))

    return layout

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    console = Console()

    if mode == "--once":
        t = time.time()
        console.print(render_frame(t))
        return

    console.print("\n[bold cyan]VidFlow AI — Pixel Office[/]")
    console.print("[dim]Ctrl+C para salir[/]\n")
    time.sleep(0.5)

    with Live(render_frame(time.time()), console=console,
              refresh_per_second=4, screen=True) as live:
        try:
            while True:
                t = time.time()
                live.update(render_frame(t))
                time.sleep(0.25)
        except KeyboardInterrupt:
            pass

    console.print("\n[dim]Monitor cerrado.[/]\n")

if __name__ == "__main__":
    main()
