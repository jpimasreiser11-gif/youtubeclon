#!/bin/bash
# ═══════════════════════════════════════════════════════════
# start.sh — Arranca TODO el sistema con un solo comando
#
# Uso:
#   bash start.sh             → ciclo único + status
#   bash start.sh --auto      → modo continuo en background
#   bash start.sh --status    → solo ver el estado
#   bash start.sh --stop      → parar el sistema
#   bash start.sh --cleanup   → limpiar archivos inútiles
#   bash start.sh --master    → prompt maestro (mejora extrema)
# ═══════════════════════════════════════════════════════════

MODE=${1:-"--once"}
mkdir -p logs briefings research .copilot/agents

case $MODE in

  # ── VER ESTADO ──────────────────────────────────────────
  "--status")
    python scripts/agent_status.py --once
    ;;

  # ── PARAR EL SISTEMA ────────────────────────────────────
  "--stop")
    if [ -f logs/master.pid ]; then
      PID=$(cat logs/master.pid)
      if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo "✅ Sistema parado (PID $PID)"
        rm logs/master.pid
      else
        echo "⚠️  El proceso ya no corría"
        rm logs/master.pid
      fi
    else
      echo "ℹ️  No hay sistema corriendo"
    fi
    ;;

  # ── MODO CONTINUO EN BACKGROUND ─────────────────────────
  "--auto")
    # Verificar APIs antes de arrancar
    echo "🔍 Verificando APIs..."
    python scripts/check_apis.py
    if [ $? -ne 0 ]; then
      echo ""
      echo "❌ Configura las APIs que faltan en .env y vuelve a ejecutar."
      echo "   Guía: SETUP.md"
      exit 1
    fi

    echo ""
    echo "🚀 Arrancando sistema autónomo en background..."
    nohup bash scripts/run_agents.sh --loop > logs/master.log 2>&1 &
    MASTER_PID=$!
    echo $MASTER_PID > logs/master.pid
    echo ""
    echo "✅ Sistema arrancado (PID $MASTER_PID)"
    echo ""
    echo "Comandos útiles:"
    echo "  Ver estado:      python scripts/agent_status.py"
    echo "  Ver logs:        tail -f logs/master.log"
    echo "  Ver briefing:    cat briefings/\$(date +%Y-%m-%d)-briefing.md"
    echo "  Parar sistema:   bash start.sh --stop"
    echo ""
    echo "El sistema trabajará en ciclos de 1 hora."
    echo "Cierra esta terminal tranquilamente — el sistema sigue corriendo."

    # Mostrar los primeros logs durante 10 segundos para confirmar arranque
    sleep 3
    echo ""
    echo "── Primeras líneas del log ────────────────────────────"
    tail -10 logs/master.log
    ;;

  # ── MODO SCHEDULER ──────────────────────────────────────
  "--schedule")
    export PYTHONPATH=$(pwd)
    echo "⏱️ Iniciando monitor de agenda (scheduler)..."
    python -m backend.scheduler
    ;;

  # ── CICLO ÚNICO ─────────────────────────────────────────
  "--once")
    echo "🔄 Ejecutando ciclo completo de agentes..."
    bash scripts/run_agents.sh --once
    echo ""
    python scripts/agent_status.py --once
    ;;

  # ── LIMPIEZA ────────────────────────────────────────────
  "--cleanup")
    echo "🧹 Iniciando limpieza del proyecto..."
    # Pasar el prompt de limpieza a Copilot
    cat prompts/CLEANUP_PROMPT.md | gh copilot suggest -t shell -
    ;;

  # ── PROMPT MAESTRO (mejora extrema) ─────────────────────
  "--master")
    echo "⚡ Activando modo mejora extrema..."
    echo "   Los agentes trabajarán hasta alcanzar el nivel máximo posible."
    echo ""

    # Crear archivo de estado inicial
    cat > STATUS.md << EOF
# Estado del Sistema — $(date '+%Y-%m-%d %H:%M')
**Iteración actual**: #1
**Criterios completados**: 0/10
**Trabajando en**: Iniciando análisis del proyecto
**Próxima tarea**: Revisar estado actual y crear backlog de mejoras
**Bloqueantes**: Ninguno detectado aún
EOF

    # Crear backlog inicial si no existe
    if [ ! -f research/improvement_backlog.md ]; then
      mkdir -p research
      cat > research/improvement_backlog.md << EOF
# Backlog de Mejoras — VidFlow AI

## Por hacer
- [ ] Pipeline sin pantalla negra
- [ ] 7 días de scripts por canal
- [ ] 10 checks de calidad al 100%
- [ ] Dashboard web funcional
- [ ] GitHub Actions configurado
- [ ] Tests automáticos
- [ ] 3 afiliados activos por canal
- [ ] Sistema trending topics
- [ ] Documentación final

## En progreso
(vacío)

## Completado
(vacío)
EOF
    fi

    # Pasar el prompt maestro a Copilot con el contexto del proyecto
    INSTRUCTIONS=$(cat .github/copilot-instructions.md 2>/dev/null || echo "")
    MASTER_PROMPT=$(cat prompts/MASTER_AUTONOMOUS_PROMPT.md)
    STATUS=$(cat STATUS.md)

    FULL_PROMPT="$INSTRUCTIONS

---

$MASTER_PROMPT

---

ESTADO ACTUAL DEL PROYECTO:
$STATUS

Lee el archivo research/improvement_backlog.md para ver qué queda por hacer.
Empieza por lo más crítico y trabaja en orden de prioridad."

    echo "$FULL_PROMPT" | gh copilot suggest -t shell -
    ;;

  # ── AYUDA ────────────────────────────────────────────────
  *)
    echo "Uso: bash start.sh [opción]"
    echo ""
    echo "  --status   Ver qué está haciendo cada agente"
    echo "  --auto     Arrancar sistema autónomo en background"
    echo "  --once     Ejecutar un ciclo completo y parar"
    echo "  --schedule Ver la agenda y monitorizar los envíos"
    echo "  --stop     Parar el sistema"
    echo "  --cleanup  Limpiar archivos inútiles del proyecto"
    echo "  --master   Modo mejora extrema (trabaja hasta el límite)"
    echo ""
    echo "Ejemplo para dejar trabajando 24h:"
    echo "  bash start.sh --auto"
    echo "  python scripts/agent_status.py   # ver en tiempo real"
    ;;
esac
