#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# run_agents.sh — Orquestador maestro de los 10 agentes
#
# Uso:
#   bash scripts/run_agents.sh          → ciclo completo
#   bash scripts/run_agents.sh --loop   → bucle infinito (mejora continua)
#   bash scripts/run_agents.sh --once   → solo una vez y para
#
# Para dejarlo corriendo en segundo plano durante horas:
#   nohup bash scripts/run_agents.sh --loop > logs/master.log 2>&1 &
#   echo $! > logs/master.pid
#
# Para pararlo:
#   kill $(cat logs/master.pid)
# ═══════════════════════════════════════════════════════════════

MODE=${1:-"--once"}
mkdir -p logs briefings research analytics monetization quality-reports code-reviews

run_cycle() {
  local DATE=$(date +%Y-%m-%d)
  local DOW=$(date +%u)   # 1=Lun ... 7=Dom
  local LOG="logs/master-$DATE.log"

  echo "" | tee -a $LOG
  echo "══════════════════════════════════════════" | tee -a $LOG
  echo " CICLO COMPLETO — $(date '+%Y-%m-%d %H:%M')" | tee -a $LOG
  echo "══════════════════════════════════════════" | tee -a $LOG

  step() {
    local num=$1
    local name=$2
    local extra=$3
    echo "" | tee -a $LOG
    echo "┌─ [$num/10] $name ─────────────────" | tee -a $LOG
    bash scripts/run_agent.sh $num "$extra" 2>&1 | tee -a $LOG
    echo "└─ $name ✓ $(date +%H:%M)" | tee -a $LOG
    sleep 5  # Pausa entre agentes para evitar rate limits
  }

  # ── FASE 1: INTELIGENCIA (siempre) ──────────────────────────
  step "09" "Trend Hunter"   "Fecha: $DATE. Busca tendencias para los 6 canales."
  step "01" "Researcher"     "Usa los trends de hoy. Investiga competencia y monetización."

  # ── FASE 2: PRODUCCIÓN (siempre) ────────────────────────────
  step "02" "Content Forge"  "Lee research de hoy y trends. Genera scripts para 6 canales."
  step "04" "SEO Engineer"   "Optimiza metadata de todos los scripts de hoy."

  # ── FASE 3: PIPELINE ────────────────────────────────────────
  echo "" | tee -a $LOG
  echo "┌─ [PIPELINE] Generando vídeos ────────────────────" | tee -a $LOG
  python pipeline/pipeline.py 2>&1 | tee -a $LOG
  echo "└─ Pipeline ✓ $(date +%H:%M)" | tee -a $LOG
  sleep 10

  # ── FASE 4: CALIDAD + SUBIDA ─────────────────────────────────
  step "05" "Quality Gate"   "Revisa todos los vídeos ensamblados hoy."
  echo "" | tee -a $LOG
  echo "┌─ [UPLOAD] Subiendo vídeos aprobados ─────────────" | tee -a $LOG
  python pipeline/youtube_uploader.py --queue pipeline_queue.json 2>&1 | tee -a $LOG
  echo "└─ Upload ✓ $(date +%H:%M)" | tee -a $LOG

  # ── FASE 5: MONITORIZACIÓN ───────────────────────────────────
  step "08" "Fixer"          "Revisa errores del ciclo de hoy y aplica fixes."

  # ── SEMANAL (solo lunes) ─────────────────────────────────────
  if [ "$DOW" = "1" ]; then
    echo "" | tee -a $LOG
    echo "▶ LUNES — Ejecutando agentes semanales..." | tee -a $LOG
    step "07" "Data Analyst"   "Genera reporte semanal completo."
    step "06" "Money Finder"   "Busca nuevas oportunidades de monetización esta semana."
  fi

  # ── CADA 3 DÍAS ──────────────────────────────────────────────
  if [ "$DOW" = "1" ] || [ "$DOW" = "4" ] || [ "$DOW" = "7" ]; then
    step "03" "Code Sentinel"  "Revisa el código del pipeline. Aplica mejoras."
  fi

  # ── BRIEFING FINAL ────────────────────────────────────────────
  step "10" "Master Scheduler" "Lee todos los outputs de hoy. Genera briefing diario."

  echo "" | tee -a $LOG
  echo "══════════════════════════════════════════" | tee -a $LOG
  echo " CICLO COMPLETO ✓ $(date '+%H:%M')" | tee -a $LOG
  echo " Briefing: briefings/$DATE-briefing.md" | tee -a $LOG
  echo "══════════════════════════════════════════" | tee -a $LOG
}

# ── MODOS DE EJECUCIÓN ────────────────────────────────────────

if [ "$MODE" = "--loop" ]; then
  echo "🔁 MODO BUCLE INFINITO — Mejora continua activa"
  echo "   Para parar: kill \$(cat logs/master.pid)"
  echo $$ > logs/master.pid

  CYCLE=1
  while true; do
    echo ""
    echo "════════════════════════════════════════"
    echo " CICLO #$CYCLE — $(date '+%Y-%m-%d %H:%M')"
    echo "════════════════════════════════════════"

    run_cycle

    CYCLE=$((CYCLE + 1))
    WAIT=3600  # Espera 1 hora entre ciclos completos

    echo ""
    echo "⏳ Esperando ${WAIT}s hasta el próximo ciclo..."
    echo "   Próximo ciclo #$CYCLE a las $(date -d "+${WAIT} seconds" +%H:%M 2>/dev/null || date -v +${WAIT}S +%H:%M)"
    sleep $WAIT
  done

elif [ "$MODE" = "--once" ]; then
  run_cycle

else
  echo "❌ Modo desconocido: $MODE"
  echo "Uso: bash scripts/run_agents.sh [--once|--loop]"
  exit 1
fi
