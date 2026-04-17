#!/usr/bin/env python3
"""
changelog_writer.py — Registra todos los cambios que hacen los agentes.
Los agentes llaman esto cuando modifican archivos.

Uso directo:
  python scripts/changelog_writer.py "Agent-02" "Generado guión Impacto Mundial — Area 51"
  python scripts/changelog_writer.py "Agent-11" "Añadida técnica open-loop a templates"

Desde Python:
  from scripts.changelog_writer import log_change
  log_change("Agent-08", "fix", "pipeline/ensamblador.py", "Arreglada pantalla negra")

Ver cambios:
  python scripts/changelog_writer.py --view
  python scripts/changelog_writer.py --view --today
"""

import sys, json, os
from datetime import datetime
from pathlib import Path

CHANGELOG_FILE = Path("logs/changelog.md")
CHANGELOG_JSON = Path("logs/changelog.json")

CHANGE_TYPES = {
    "fix":      ("🔧", "red"),
    "feat":     ("✨", "green"),
    "content":  ("✍️ ", "magenta"),
    "research": ("🔍", "cyan"),
    "improve":  ("📈", "blue"),
    "delete":   ("🗑️ ", "dim"),
    "alert":    ("🚨", "red"),
    "info":     ("📝", "white"),
}

def log_change(agent: str, change_type: str, file_path: str, description: str):
    """Registra un cambio en el changelog"""
    now = datetime.now()
    entry = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M"),
        "agent": agent,
        "type": change_type,
        "file": file_path,
        "description": description,
    }

    # Crear directorio si no existe
    CHANGELOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Añadir a JSON (para el dashboard)
    entries = []
    if CHANGELOG_JSON.exists():
        try:
            entries = json.loads(CHANGELOG_JSON.read_text())
        except:
            entries = []
    entries.append(entry)
    # Mantener solo los últimos 500 entries
    entries = entries[-500:]
    CHANGELOG_JSON.write_text(json.dumps(entries, indent=2, ensure_ascii=False))

    # Añadir a Markdown (para lectura humana)
    emoji = CHANGE_TYPES.get(change_type, ("📝", "white"))[0]
    line = f"[{now.strftime('%H:%M')}] {emoji} [{agent}] {description}"
    if file_path:
        line += f" → `{file_path}`"
    line += "\n"

    # Añadir header de fecha si es un nuevo día
    md_content = CHANGELOG_FILE.read_text() if CHANGELOG_FILE.exists() else ""
    today_header = f"## {now.strftime('%Y-%m-%d')}\n"
    if today_header not in md_content:
        line = "\n" + today_header + line

    with CHANGELOG_FILE.open("a", encoding="utf-8") as f:
        f.write(line)

    return entry

def view_changelog(today_only=False, last_n=20):
    """Muestra el changelog en la terminal con colores"""
    try:
        from rich.console import Console
        from rich.table import Table
        from rich import box as rbox
        console = Console()
    except ImportError:
        # Fallback sin rich
        if CHANGELOG_FILE.exists():
            print(CHANGELOG_FILE.read_text())
        return

    entries = []
    if CHANGELOG_JSON.exists():
        try:
            entries = json.loads(CHANGELOG_JSON.read_text())
        except:
            pass

    if today_only:
        today = datetime.now().strftime("%Y-%m-%d")
        entries = [e for e in entries if e.get("date") == today]

    entries = entries[-last_n:]

    if not entries:
        console.print("[dim]Sin cambios registrados todavía.[/dim]")
        return

    table = Table(
        title=f"[bold]Changelog — {'Hoy' if today_only else f'Últimos {last_n}'}[/]",
        box=rbox.ROUNDED,
        show_header=True,
        header_style="bold dim",
    )
    table.add_column("Hora", width=6, style="dim")
    table.add_column("Agente", width=12)
    table.add_column("Tipo", width=8)
    table.add_column("Descripción", min_width=40)
    table.add_column("Archivo", style="dim", min_width=20)

    for e in reversed(entries):
        emoji, color = CHANGE_TYPES.get(e.get("type", "info"), ("📝", "white"))
        table.add_row(
            e.get("time", "??:??"),
            f"[{color}]{e.get('agent', '?')}[/]",
            f"{emoji} {e.get('type', '?')}",
            e.get("description", ""),
            e.get("file", "") or "",
        )

    console.print(table)

def main():
    args = sys.argv[1:]

    if not args or args[0] == "--view":
        today_only = "--today" in args
        view_changelog(today_only=today_only)
        return

    if len(args) >= 2:
        agent = args[0]
        description = args[1]
        change_type = args[2] if len(args) > 2 else "info"
        file_path = args[3] if len(args) > 3 else ""
        entry = log_change(agent, change_type, file_path, description)
        print(f"✅ Registrado: [{entry['time']}] {entry['agent']} — {entry['description']}")
    else:
        print("Uso: python scripts/changelog_writer.py AGENTE DESCRIPCIÓN [tipo] [archivo]")
        print("     python scripts/changelog_writer.py --view [--today]")

if __name__ == "__main__":
    main()
