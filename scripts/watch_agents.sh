#!/bin/bash
# ─────────────────────────────────────────────────────────
# watch_agents.sh — Monitor en tiempo real del sistema
#
# Uso: bash scripts/watch_agents.sh
# Muestra: qué agente está corriendo, logs en vivo,
#          últimos briefings y estado del pipeline
# ─────────────────────────────────────────────────────────

clear

print_header() {
  echo "╔══════════════════════════════════════════════════════╗"
  echo "║         VidFlow AI — Monitor de Agentes              ║"
  echo "║         $(date '+%Y-%m-%d %H:%M:%S')                         ║"
  echo "╚══════════════════════════════════════════════════════╝"
}

print_agent_status() {
  echo ""
  echo "── ESTADO DE AGENTES ──────────────────────────────────"
  for i in 01 02 03 04 05 06 07 08 09 10; do
    local names=(
      [01]="Researcher  " [02]="ContentForge" [03]="CodeSentinel"
      [04]="SEO Engineer" [05]="Quality Gate" [06]="MoneyFinder "
      [07]="DataAnalyst " [08]="Fixer       " [09]="TrendHunter "
      [10]="Scheduler   "
    )
    local name=${names[$i]}
    local memory=".copilot/agents/agent-${i}-*/memory.json"

    # Busca la última ejecución en memory.json si existe
    local last_run=""
    for f in .copilot/agents/agent-$i-*/memory.json; do
      if [ -f "$f" ]; then
        last_run=$(python3 -c "import json; d=json.load(open('$f')); print(d.get('last_run','never'))" 2>/dev/null)
      fi
    done

    if [ -z "$last_run" ]; then last_run="nunca"; fi
    echo "  [$i] $name  último run: $last_run"
  done
}

print_pipeline_queue() {
  echo ""
  echo "── COLA DE VÍDEOS ─────────────────────────────────────"
  if [ -f "pipeline_queue.json" ]; then
    python3 -c "
import json, sys
try:
    q = json.load(open('pipeline_queue.json'))
    if not q:
        print('  (cola vacía)')
    else:
        statuses = {}
        for v in q:
            s = v.get('status','UNKNOWN')
            statuses[s] = statuses.get(s, 0) + 1
        for status, count in sorted(statuses.items()):
            emoji = {'UPLOADED':'✅','APPROVED':'🔵','FIX_REQUIRED':'🔴',
                     'GENERATING':'🟡','QUALITY_CHECK':'🔍','PENDING':'⬜'}.get(status,'❓')
            print(f'  {emoji} {status}: {count} vídeo(s)')
except:
    print('  (no se puede leer pipeline_queue.json)')
" 2>/dev/null
  else
    echo "  (pipeline_queue.json no encontrado)"
  fi
}

print_latest_briefing() {
  echo ""
  echo "── ÚLTIMO BRIEFING ────────────────────────────────────"
  local latest=$(ls -t briefings/*.md 2>/dev/null | head -1)
  if [ -n "$latest" ]; then
    echo "  📋 $latest"
    head -20 "$latest" | sed 's/^/  /'
  else
    echo "  (sin briefings todavía)"
  fi
}

print_live_log() {
  echo ""
  echo "── LOG EN VIVO (últimas 10 líneas) ────────────────────"
  local latest_log=$(ls -t logs/master-*.log 2>/dev/null | head -1)
  if [ -n "$latest_log" ]; then
    tail -10 "$latest_log" | sed 's/^/  /'
  else
    echo "  (sin logs todavía — arranca: bash scripts/run_agents.sh --loop)"
  fi
}

print_master_pid() {
  echo ""
  echo "── PROCESO MASTER ─────────────────────────────────────"
  if [ -f "logs/master.pid" ]; then
    local pid=$(cat logs/master.pid)
    if kill -0 $pid 2>/dev/null; then
      echo "  ✅ Sistema corriendo (PID $pid)"
      echo "  Para parar: kill $pid"
    else
      echo "  ⛔ Sistema parado (último PID: $pid)"
      echo "  Para arrancar: nohup bash scripts/run_agents.sh --loop > logs/master.log 2>&1 &"
    fi
  else
    echo "  ⛔ Sistema no iniciado"
    echo "  Para arrancar: nohup bash scripts/run_agents.sh --loop > logs/master.log 2>&1 &"
  fi
  echo ""
}

# Ejecutar en bucle actualizando cada 10 segundos
while true; do
  clear
  print_header
  print_master_pid
  print_agent_status
  print_pipeline_queue
  print_latest_briefing
  print_live_log
  echo ""
  echo "  Actualizando en 10s... (Ctrl+C para salir)"
  sleep 10
done
