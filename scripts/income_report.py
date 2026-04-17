import json
import os
from datetime import datetime, timedelta
from pathlib import Path

ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRACKER_FILE = ROOT_DIR / "monetization" / "income_tracker.json"
REPORTS_DIR = ROOT_DIR / "income_reports"

def generate_weekly_report():
    REPORTS_DIR.mkdir(exist_ok=True)
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    report_name = f"weekly-{monday.strftime('%Y-%m-%d')}.md"
    report_path = REPORTS_DIR / report_name

    if not TRACKER_FILE.exists():
        TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with TRACKER_FILE.open("w", encoding="utf-8") as f:
            json.dump([], f)
        entries = []
    else:
        try:
            with TRACKER_FILE.open("r", encoding="utf-8-sig") as f:
                entries = json.load(f)
            if not isinstance(entries, list):
                entries = []
        except:
            entries = []

    # Calculate totals
    total_estimated = sum(float(e.get("estimated_monthly", 0)) for e in entries)
    
    # Group by source
    by_source = {}
    for e in entries:
        src = e.get("source", "Unknown")
        by_source[src] = by_source.get(src, 0) + float(e.get("estimated_monthly", 0))

    # Generate markdown report
    markdown = f"""# Informe de Ingresos — Semana del {monday.strftime('%Y-%m-%d')}

## Resumen ejecutivo
El equipo de monetización ha actualizado sus estimaciones para esta semana.
Actualmente el sistema está estimando un total proyectado de **${total_estimated:.2f}**/mes
basado en las fuentes activas reportadas por los agentes.

## Ingresos esta semana (estimados)
| Fuente | Canal | Estimado | Confianza | Agente |
|--------|-------|----------|-----------|--------|
"""
    if not entries:
        markdown += "| (Sin datos) | - | $0.00 | - | - |\n"
    else:
        # Deduplicate visually if necessary, or just list all
        for e in entries:
            ch = e.get("channel", "global")
            est = float(e.get("estimated_monthly", 0))
            conf = e.get("confidence", "low")
            ag = e.get("agent", "?")
            src = e.get("source", "Unknown")
            markdown += f"| {src} | {ch} | ${est:.2f} | {conf} | {ag} |\n"

    markdown += f"| **TOTAL PROYECTADO** | | **${total_estimated:.2f}** | | |\n\n"

    markdown += """## Próximos hitos de monetización
- [Wealth Files] alcanza hitos de retención → YPP: estimado en 14 días
- [El Loco de la IA] programa de referidos de herramientas AI activo

## Lo que más ha contribuido esta semana
Pendiente de confirmación de analytics reales vs estimados.

## Lo que menos ha funcionado
En monitoreo por Agent-22 (AB Testing).
"""

    with report_path.open("w", encoding="utf-8") as f:
        f.write(markdown)
    
    print(f"Reporte generado: {report_path}")
    return report_path

if __name__ == "__main__":
    generate_weekly_report()
