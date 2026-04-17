---
name: vidflow-agent-system
description: >
  Complete VidFlow AI agent system skill for OpenClaw. Use this skill
  when any VidFlow agent needs to: execute pipeline tasks, communicate
  with other agents, update income tracking, generate content, check system
  status, or send reports to the human. Trigger on: any VidFlow system
  operation, pipeline execution, agent coordination, income reporting,
  content generation for the 6 channels, or system improvement tasks.
---

# VidFlow Agent System — OpenClaw Skill

## The 6 Channels
- Impacto Mundial (ES) — mystery, conspiracy, paranormal
- Mentes Rotas (ES) — true crime, criminal psychology
- El Loco de la IA (ES) — free AI tools, automation
- Mind Warp (EN) — dark psychology, cognitive biases
- Wealth Files (EN) — billionaire empires, dark money
- Dark Science (EN) — universe mysteries, quantum physics

## Core File Locations
```
~/vidflow-project/
├── pipeline/          — main pipeline code
├── content_calendars/ — scripts per channel
├── pipeline_queue.json — video production status
├── monetization/      — income tracking
├── research/          — research outputs
├── diary/             — agent diaries
├── STATUS_BOARD.md    — current system status
└── NEEDS_FROM_HUMAN.md — requests for the human
```

## How Agents Communicate (OpenClaw-aware)
Each agent reads shared files at start of session:
```
shared-memory/team_updates.md    — messages from other agents
shared-memory/income_tracker.json — current income status
pipeline_queue.json              — video production queue
```

Agents write to:
```
diary/agent-XX-diary.md          — daily diary entry
diary/team-updates.md            — messages for the team
NEEDS_FROM_HUMAN.md              — requests for human help
```

## Pipeline Execution Commands
```bash
# Run full daily cycle
python pipeline/pipeline.py

# Run specific agent task
bash scripts/run_agent.sh [agent-number]

# Check system status
python scripts/agent_status.py --once

# View today's income
python -c "
import json
data = json.load(open('monetization/income_tracker.json'))
total = sum(e.get('estimated_monthly', 0) for e in data)
print(f'Estimated monthly: \${total:.2f}')
"

# Generate today's prompt from calendar
python scripts/generate_calendar.py --today
```

## Income Reporting Protocol
Every agent that touches revenue MUST update:
`monetization/income_tracker.json`

```json
{
  "date": "YYYY-MM-DD",
  "agent": "Agent-06",
  "source": "Amazon Associates",
  "channel": "wealth-files",
  "estimated_monthly": 45.00,
  "confidence": "medium",
  "notes": "3 active links, ~200 clicks/month estimated"
}
```

## Daily Report Format (sent via Telegram at 20:00)
```
📊 VIDFLOW AI — Informe Diario
[Fecha]

💰 INGRESOS HOY
[itemized by source]
Total mes hasta hoy: $X

✅ COMPLETADO HOY
[2-3 lines of what agents did]

📹 VÍDEOS
Generados: X | Subidos: X | En cola: X

⚠️ NECESITAS HACER
[only if urgent]

🎯 MAÑANA
[preview of tomorrow's work]
```

## Self-Improvement Loop
Every agent includes in their heartbeat:
1. Evaluate: did my work today contribute to income? How?
2. Improve: what would I do differently tomorrow?
3. Learn: what did I discover that I didn't know before?
4. Document: write it in diary so the next session remembers

## Safety Rules (hardcoded, never override)
- Never modify .env file
- Never delete files from git history
- Never send credentials over chat
- Never approve payments without human confirmation
- Never create accounts that require payment methods
- Always backup before modifying pipeline code
