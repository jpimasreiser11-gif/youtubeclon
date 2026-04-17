#!/usr/bin/env python3
"""
patriarch_runner.py — Arranca al Patriarca y muestra su diario en vivo.

Uso:
  python scripts/patriarch_runner.py           # diary en tiempo real
  python scripts/patriarch_runner.py --once    # una iteración y para
  python scripts/patriarch_runner.py --board   # solo el STATUS_BOARD
"""

import os, sys, time, json, glob
from datetime import datetime
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.columns import Columns
    from rich.text import Text
    from rich.live import Live
    from rich.layout import Layout
    from rich.rule import Rule
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

MODE = sys.argv[1] if len(sys.argv) > 1 else "--watch"

DIARY_FILE   = Path("diary/patriarch-diary.md")
STATUS_FILE  = Path("STATUS_BOARD.md")
INBOX_BASE   = Path(".copilot/agents")

def ensure_dirs():
    Path("diary").mkdir(exist_ok=True)
    for num in ["00","01","02","03","04","05","06","07","08","09","10","11"]:
        for pattern in [f".copilot/agents/agent-{num}-*",
                        f"agents-system/agent-{num}-*"]:
            for d in glob.glob(pattern):
                Path(d, "inbox").mkdir(exist_ok=True)

def read_diary(n_lines=40):
    if not DIARY_FILE.exists():
        return "El Patriarca aún no ha escrito nada. Esperando primer ciclo..."
    lines = DIARY_FILE.read_text(encoding="utf-8").split("\n")
    return "\n".join(lines[-n_lines:])

def read_status_board():
    if not STATUS_FILE.exists():
        return "STATUS_BOARD.md no generado aún."
    return STATUS_FILE.read_text(encoding="utf-8")

def read_changelog(n=12):
    changelog = Path("logs/changelog.json")
    if not changelog.exists():
        return []
    try:
        entries = json.loads(changelog.read_text())
        return entries[-n:]
    except:
        return []

def read_inboxes():
    """Lee todos los mensajes pendientes del Patriarca a los agentes"""
    messages = []
    for inbox_file in sorted(Path(".copilot/agents").rglob("inbox/message-*.md")):
        try:
            content = inbox_file.read_text(encoding="utf-8")
            lines = content.strip().split("\n")
            to_line = next((l for l in lines if l.startswith("TO:")), "")
            msg_preview = " ".join(lines[4:6]) if len(lines) > 4 else ""
            messages.append({
                "file": str(inbox_file),
                "to": to_line.replace("TO:","").strip(),
                "preview": msg_preview[:70],
            })
        except:
            pass
    return messages[-5:]

def write_diary_entry(text: str):
    """El Patriarca escribe una entrada en su diario"""
    DIARY_FILE.parent.mkdir(exist_ok=True)
    now = datetime.now().strftime("%H:%M")
    entry = f"\n{now} — {text}\n"
    with DIARY_FILE.open("a", encoding="utf-8") as f:
        f.write(entry)

def write_status_board(text: str):
    STATUS_FILE.write_text(text, encoding="utf-8")

def write_inbox_message(to_agent: str, message: str, from_agent="Agent-00"):
    """Envía un mensaje a la bandeja de entrada de un agente"""
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d-%H")
    # Find agent folder
    for pattern in [f".copilot/agents/agent-{to_agent}-*",
                    f"agents-system/agent-{to_agent}-*"]:
        folders = glob.glob(pattern)
        if folders:
            inbox = Path(folders[0], "inbox")
            inbox.mkdir(exist_ok=True)
            msg_file = inbox / f"message-{timestamp}.md"
            msg_file.write_text(
                f"FROM: {from_agent} (Patriarch)\n"
                f"TO: {to_agent}\n"
                f"TIME: {now.strftime('%H:%M')}\n\n"
                f"{message}\n",
                encoding="utf-8"
            )
            return str(msg_file)
    return None

def run_patriarch_cycle():
    """Ejecuta un ciclo del Patriarca"""
    now = datetime.now().strftime("%H:%M")
    ensure_dirs()

    # Leer estado de todos los agentes
    agent_states = {}
    for num in ["01","02","03","04","05","06","07","08","09","10","11"]:
        for pattern in [f".copilot/agents/agent-{num}-*/memory.json",
                        f"agents-system/agent-{num}-*/memory.json"]:
            files = glob.glob(pattern)
            if files:
                try:
                    mem = json.loads(Path(files[0]).read_text())
                    agent_states[num] = mem
                except:
                    agent_states[num] = {}
                break

    # Leer changelog reciente
    changelog = read_changelog(20)

    # Generar entrada de diario
    working_agents = [n for n, s in agent_states.items() if s.get("running") or s.get("status") == "working"]
    done_today = [e for e in changelog if e.get("date") == datetime.now().strftime("%Y-%m-%d")]

    if working_agents:
        diary_text = (
            f"El equipo está activo ahora mismo. "
            f"{'Agent-0'+working_agents[0] if working_agents else ''} está trabajando"
            f"{', junto con ' + ', '.join('Agent-0'+n for n in working_agents[1:]) if len(working_agents)>1 else ''}. "
            f"Llevamos {len(done_today)} cambios registrados hoy. "
            f"Todo parece ir bien de momento."
        )
    else:
        diary_text = (
            f"El equipo está en pausa ahora mismo. "
            f"Se han registrado {len(done_today)} cambios hoy. "
            f"Esperando el próximo ciclo programado."
        )

    write_diary_entry(diary_text)

    # Actualizar STATUS_BOARD
    status_text = f"""# VidFlow AI — What's Happening Right Now
Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

## The team is working on...
"""
    if working_agents:
        for n in working_agents:
            task = agent_states.get(n, {}).get("current_task", "trabajando...")
            status_text += f"Agent {n} — {task}\n"
    else:
        status_text += "Todos los agentes en reposo. Próximo ciclo programado.\n"

    status_text += "\n## Done today\n"
    for entry in done_today[-5:]:
        icon = {"fix":"🔧","feat":"✨","content":"✍️","research":"🔍"}.get(entry.get("type",""),"✅")
        status_text += f"{icon} {entry.get('agent','?')} — {entry.get('description','')}\n"
    if not done_today:
        status_text += "Nada registrado aún hoy.\n"

    # Necesidades pendientes
    needs_file = Path("NEEDS_FROM_HUMAN.md")
    if needs_file.exists():
        needs_lines = [l for l in needs_file.read_text().split("\n") if "- [ ]" in l]
        if needs_lines:
            status_text += "\n## Needs your attention\n"
            for line in needs_lines[:3]:
                status_text += f"⚠️ {line.strip()[5:].strip()}\n"

    write_status_board(status_text)
    return diary_text

def display_rich():
    console = Console()

    def make_layout():
        diary_txt = read_diary(30)
        board_txt = read_status_board()
        changelog = read_changelog(10)
        messages  = read_inboxes()

        layout = Layout()
        layout.split_row(
            Layout(name="left",  ratio=3),
            Layout(name="right", ratio=2),
        )
        layout["left"].split_column(
            Layout(name="diary",  ratio=3),
            Layout(name="board",  ratio=2),
        )
        layout["right"].split_column(
            Layout(name="changes"),
            Layout(name="inbox"),
        )

        # Diary panel
        diary_renderable = Text(diary_txt, style="dim white")
        layout["diary"].update(Panel(
            diary_renderable,
            title="[bold yellow]📖 Diario del Patriarca[/]",
            border_style="yellow",
        ))

        # Status board
        layout["board"].update(Panel(
            Text(board_txt[:600], style="white"),
            title="[bold cyan]📋 STATUS BOARD[/]",
            border_style="cyan",
        ))

        # Changelog
        changes_txt = Text()
        for e in reversed(changelog):
            icon = {"fix":"🔧","feat":"✨","content":"✍️","research":"🔍","alert":"🚨"}.get(e.get("type",""),"📝")
            changes_txt.append(f"{e.get('time','??:??')} ", style="dim")
            changes_txt.append(f"{icon} ", style="white")
            changes_txt.append(f"{e.get('agent','?')} ", style="bold cyan")
            changes_txt.append(f"{e.get('description','')[:45]}\n", style="dim")
        layout["changes"].update(Panel(
            changes_txt or Text("Sin cambios aún", style="dim"),
            title="[bold green]📝 Cambios recientes[/]",
            border_style="green",
        ))

        # Inbox messages
        inbox_txt = Text()
        if messages:
            for m in messages:
                inbox_txt.append(f"→ {m['to']}\n", style="bold magenta")
                inbox_txt.append(f"  {m['preview']}\n", style="dim")
        else:
            inbox_txt.append("Sin mensajes pendientes", style="dim")
        layout["inbox"].update(Panel(
            inbox_txt,
            title="[bold magenta]📬 Mensajes del Patriarca[/]",
            border_style="magenta",
        ))

        return layout

    if MODE == "--board":
        console.print(Panel(read_status_board(), title="[bold cyan]STATUS BOARD[/]", border_style="cyan"))
        return

    with Live(make_layout(), console=console, refresh_per_second=2, screen=True) as live:
        try:
            while True:
                run_patriarch_cycle()
                live.update(make_layout())
                time.sleep(30)
        except KeyboardInterrupt:
            pass

def display_plain():
    while True:
        run_patriarch_cycle()
        print("\n" + "="*60)
        print(read_status_board())
        print("="*60)
        print(read_diary(15))
        if MODE == "--once":
            break
        time.sleep(30)

def main():
    ensure_dirs()
    if MODE == "--once":
        run_patriarch_cycle()
        if HAS_RICH:
            Console().print(Panel(read_status_board(), title="STATUS BOARD", border_style="cyan"))
            Console().print(Panel(read_diary(10), title="Diario", border_style="yellow"))
        else:
            print(read_status_board())
            print(read_diary(10))
        return

    if HAS_RICH:
        display_rich()
    else:
        print("Instala rich para mejor visualización: pip install rich")
        display_plain()

if __name__ == "__main__":
    main()
