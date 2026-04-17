# youtube-auto-pro-system

Master skill for YouTube Automation Pro.
Use when working on any project area: pipeline, frontend, marketing, skills, setup, or deployment.

## System map
- Backend API: `backend/server.py` + `backend/routes/*`
- Pipeline: `backend/pipeline/*`
- Frontend dashboard: `frontend/src/*`
- Design system: `design-system/*`
- Marketing strategy: `marketing/phase2/*`
- Brand assets: `assets/brand/*`
- Tests/reporting: `tests/*`

## Key technical decisions
1. SQLite shared state for fast local operation and explicit logging.
2. Ordered fallback chains for external providers.
3. Soft quota management via `api_usage` aggregation.
4. Channel-specific behavior driven by configuration, not duplicated code.

## Troubleshooting quick paths
- API not starting: check `.env`, DB path, dependency install.
- TTS fails: verify keys; fallback should degrade to edge/gTTS.
- No B-roll: check pexels/pixabay keys and network.
- Frontend errors: rebuild with `npm run build`.
- Pipeline errors: inspect `pipeline_logs` and module-specific logs.

