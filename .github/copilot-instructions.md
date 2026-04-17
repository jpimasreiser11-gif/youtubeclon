# VidFlow AI — Copilot Instructions

## Project Identity
This is **VidFlow AI**: a fully automated YouTube + TikTok content pipeline
for 6 channels. Your job is to build, improve, and maintain this system
using the skills and agents defined in this project.

---

## Skills Available
Always check if a skill applies before answering or writing code.
Skills are in `.github/skills/`. Load the relevant `SKILL.md` before acting.

| Trigger phrase | Skill to load |
|---|---|
| "generate content", "script", "guion", "tiktok", channel names | `.github/skills/viral-content-custom/SKILL.md` |
| "SEO", "title", "description", "keyword", "thumbnail" | `.github/skills/marketing-skills/SKILL.md` |
| "refactor", "clean code", "review", "bug", "fix code" | `.github/skills/refactoring/SKILL.md` |
| "test", "pytest", "verify", "check pipeline" | `.github/skills/webapp-testing/SKILL.md` |
| "dashboard", "UI", "React", "component", "frontend" | `.github/skills/frontend-design/SKILL.md` |
| "design", "UX", "interface", "modal", "card" | `.github/skills/ui-ux-pro-max/SKILL.md` |

**Rule**: Before writing ANY content for the 6 channels, ALWAYS read
`.github/skills/viral-content-custom/SKILL.md` (or `.github/skills/viral-content/SKILL.md`).

---

## The 6 Channels

| Channel | Language | Niche | RPM Target |
|---|---|---|---|
| Impacto Mundial | ES | Misterios históricos, conspiraciones | $6–10 |
| Mentes Rotas | ES | True crime, psicología criminal | $8–13 |
| El Loco de la IA | ES | IA gratuita, automatización, ganar dinero | $10–14 |
| Mind Warp | EN | Dark psychology, cognitive biases | $12–18 |
| Wealth Files | EN | Billionaire empires, dark money | $14–20 |
| Dark Science | EN | Universe mysteries, quantum, deep ocean | $9–14 |

---

## The 23 Agents
Agents are in `.github/agents/` and executed by `scripts/run_agents.ps1`.

| # | Agent | Purpose |
|---|---|---|
| 01 | coordinator | Coordina el equipo y valida configuración |
| 02 | research-trends | Tendencias y contexto factual |
| 03 | script-director | Estructura narrativa y retención |
| 04 | voice-audio | Calidad de voz/audio |
| 05 | footage-curator | Curación de clips y continuidad visual |
| 06 | video-editor | Validación de edición/final cut |
| 07 | thumbnail-seo | Thumbnail, títulos y metadata |
| 08 | qa-guardian | QA smoke y control de calidad |
| 09 | automation-ops | CI/CD y operación técnica |
| 10 | growth-marketing | Distribución y crecimiento |
| 11 | ui-evolution | Evolución UX/UI |
| 12 | performance | Baselines de rendimiento |
| 13 | adsense-web | Superficies web de monetización |
| 14 | affiliate | Pipeline de afiliación |
| 15 | digital-products | Roadmap de productos digitales |
| 16 | sponsorship | Gestión de patrocinio |
| 17 | newsletter | Plan de newsletter |
| 18 | shorts | Inventario shorts/clips |
| 19 | distribution | Checklist multicanal |
| 20 | system-seller | Posicionamiento de oferta/sistema |
| 21 | community | Playbook de comunidad |
| 22 | abtesting | Backlog de experimentos A/B |
| 23 | virality | Señales de viralidad |

Run a single agent profile:
```powershell
Get-Content .github\agents\01-coordinator.agent.md
```

Run all agents (Windows / PowerShell):
```powershell
powershell -ExecutionPolicy Bypass -File .\start.ps1 --auto
```

---

## Project File Map

```
vidflow-project/
├── .github/
│   ├── copilot-instructions.md   ← YOU ARE HERE
│   └── workflows/
│       ├── daily_pipeline.yml    ← GitHub Actions (runs 6:00 AM daily)
│       └── weekly_report.yml     ← GitHub Actions (runs Monday 8:00 AM)
├── .github/
│   ├── agents/                   ← 23 agent .agent.md files
│   └── skills/                   ← SKILL.md activables en Copilot CLI
├── pipeline/
│   ├── pipeline.py               ← Master pipeline orchestrator
│   ├── generador_guion.py        ← Gemini script generation
│   ├── downloader_footage.py     ← Pexels + Pixabay footage
│   ├── ensamblador_pro.py        ← ffmpeg assembly
│   ├── quality_control.py        ← 7 automated checks
│   ├── youtube_uploader.py       ← YouTube API upload
│   └── tiktok_clipper.py         ← Vertical clip for TikTok
├── content_calendars/            ← Scripts per channel per day
│   ├── impacto-mundial/
│   ├── mentes-rotas/
│   ├── el-loco-ia/
│   ├── mind-warp/
│   ├── wealth-files/
│   └── dark-science/
├── research/                     ← Agent 01 daily reports
├── analytics/                    ← Agent 07 weekly reports
├── monetization/                 ← Agent 06 tracking
├── briefings/                    ← Agent 10 daily briefings
├── logs/                         ← All pipeline + agent logs
├── scripts/
│   ├── run_agents.ps1            ← Master runner script (Windows)
│   ├── agent_status.py           ← Monitor terminal en vivo
│   ├── dashboard_server.py       ← Dashboard web/API en vivo
│   └── check_apis.py             ← Verify all API keys work
├── pipeline_queue.json           ← Video production queue
├── .env                          ← API keys (never commit)
└── requirements.txt              ← Python dependencies
```

---

## Coding Rules (apply to ALL code)

1. **Error handling**: Every function that calls an external API MUST have try/except
2. **Retry logic**: Failed API calls retry 3 times with exponential backoff (1s, 2s, 4s)
3. **API keys**: Always from `.env` via `os.getenv()` — NEVER hardcoded
4. **Logging**: Every significant action logs to `logs/` with timestamp + channel name
5. **Comments**: In Spanish (the human prefers Spanish)
6. **Cost**: Total must be $0 — flag any paid service and find a free alternative
7. **After fixing**: Always run `python -m pytest tests/ -v` to verify nothing broke

---

## API Keys Required (all free)

| Variable | Service | Get it at |
|---|---|---|
| GEMINI_API_KEY | Gemini 2.5 Pro | aistudio.google.com |
| PEXELS_API_KEY | Stock footage | pexels.com/api |
| PIXABAY_API_KEY | Stock footage | pixabay.com/api/docs |
| ELEVENLABS_API_KEY | Voice synthesis | elevenlabs.io → Profile |
| MONGODB_URL | Database | mongodb.com/atlas |
| YOUTUBE_CLIENT_ID | YouTube upload | console.cloud.google.com |
| YOUTUBE_CLIENT_SECRET | YouTube upload | console.cloud.google.com |
| EMAIL_APP_PASSWORD | Error alerts | Google → Security → App Passwords |

---

## Pipeline Queue Schema

Every video goes through these statuses in `pipeline_queue.json`:
```
PENDING → GENERATING → ASSEMBLED → QUALITY_CHECK →
APPROVED → UPLOADING → UPLOADED
         ↓                      ↓
    FIX_REQUIRED          CONTENT_REVISION
         ↓                      ↓
    Agent 08 fixes        Agent 02 rewrites
```

---

## Content Anti-Ban Rules (CRITICAL)

All generated content MUST follow these rules or it gets REJECTED:
- Hook = question or shocking statement (NEVER creator introduction)
- Conspiracy framing: always "theory", "some claim", "documents suggest"
- True crime: only court records and documented facts
- No unverified accusations against living named individuals
- No medical claims presented as absolute fact
- Must have a twist/reveal at ~70% of the video

---

## Agent Communication Protocol

Agents communicate by writing to shared JSON files:
- Agent 09 → writes automation/ops signals used by growth and coordinator
- Agent 02/03 → feed script and narrative inputs for media chain (04-07)
- Agent 08 (QA) → writes quality outcomes consumed by ops/fixer flows
- Agent 10 and monetization agents (14-23) → update growth artifacts and reports
- Every cycle writes telemetry to `logs/agents-events.jsonl` and `logs/agent-progress/`

**No agent modifies another agent's output files directly.**
Agents communicate by updating the queue status and leaving notes
in their designated output folders.
