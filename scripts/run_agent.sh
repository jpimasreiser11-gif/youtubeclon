#!/bin/bash
# ─────────────────────────────────────────────────
# run_agent.sh — Run a single agent
# Usage:
#   bash scripts/run_agent.sh 01
#   bash scripts/run_agent.sh researcher
#   bash scripts/run_agent.sh content "canal: Impacto Mundial"
# ─────────────────────────────────────────────────

AGENT_ID=$1
CONTEXT=$2
DATE=$(date +%Y-%m-%d\ %H:%M)

# Map short names to agent folders
declare -A AGENT_MAP
AGENT_MAP["01"]="agent-01-researcher"
AGENT_MAP["02"]="agent-02-content"
AGENT_MAP["03"]="agent-03-code-sentinel"
AGENT_MAP["04"]="agent-04-seo"
AGENT_MAP["05"]="agent-05-quality"
AGENT_MAP["06"]="agent-06-money"
AGENT_MAP["07"]="agent-07-analytics"
AGENT_MAP["08"]="agent-08-fixer"
AGENT_MAP["09"]="agent-09-trends"
AGENT_MAP["10"]="agent-10-scheduler"
AGENT_MAP["researcher"]="agent-01-researcher"
AGENT_MAP["content"]="agent-02-content"
AGENT_MAP["code"]="agent-03-code-sentinel"
AGENT_MAP["seo"]="agent-04-seo"
AGENT_MAP["quality"]="agent-05-quality"
AGENT_MAP["money"]="agent-06-money"
AGENT_MAP["analytics"]="agent-07-analytics"
AGENT_MAP["fixer"]="agent-08-fixer"
AGENT_MAP["trends"]="agent-09-trends"
AGENT_MAP["scheduler"]="agent-10-scheduler"

FOLDER="${AGENT_MAP[$AGENT_ID]}"

if [ -z "$FOLDER" ]; then
  echo "❌ Agent '$AGENT_ID' not found."
  echo "Available: 01-10, or: researcher, content, code, seo, quality, money, analytics, fixer, trends, scheduler"
  exit 1
fi

AGENT_PATH=".copilot/agents/$FOLDER/AGENT.md"

if [ ! -f "$AGENT_PATH" ]; then
  echo "❌ Agent file not found: $AGENT_PATH"
  exit 1
fi

echo "[$DATE] ▶ Running $FOLDER..."

# Build the prompt: instructions file + optional context
INSTRUCTIONS=$(cat .github/copilot-instructions.md)
AGENT_PROMPT=$(cat "$AGENT_PATH")

if [ -n "$CONTEXT" ]; then
  FULL_PROMPT="$INSTRUCTIONS

---

$AGENT_PROMPT

---

ADDITIONAL CONTEXT FOR THIS RUN:
$CONTEXT"
else
  FULL_PROMPT="$INSTRUCTIONS

---

$AGENT_PROMPT"
fi

# Run with Copilot CLI
echo "$FULL_PROMPT" | gh copilot suggest -t shell -

echo "[$DATE] ✓ $FOLDER completed"
