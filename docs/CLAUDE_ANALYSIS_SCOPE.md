# Claude Analysis Scope (Recommended)

Use this scope to keep analysis fast and focused on production code.

## Include (high priority)

- `app/app/**`
- `app/lib/**`
- `app/components/**`
- `app/scripts/**`
- `viral_video_system/modules/**`
- `viral_video_system/pipeline.py`
- `scripts/**`
- `migrations/**`
- `docker-compose.yml`
- `Dockerfile`
- `app/package.json`
- `requirements.txt`
- `requirements_viral_system.txt`

## Exclude (heavy or low-signal)

- `app/.next/**`
- `app/node_modules/**`
- `app/data/**`
- `app/storage/**`
- `app/output/**`
- `app/logs/**`
- `output/**`
- `output_test/**`
- `data/**`
- `data_test/**`
- `viral_video_system/temp/**`
- `venv_sovereign/**`
- `postgres_data/**`
- `redis_data/**`
- `openrouter/**`
- `_old_project_backup/**`
- `_old_project_v1_backup/**`
- `app - copia/**`
- `*.log`

## Practical prompt to Claude

"Analyze architecture, bugs, and regressions only in the include paths listed in docs/CLAUDE_ANALYSIS_SCOPE.md, and ignore everything in the exclude list. Prioritize app/scripts, app/api routes, worker/queue flow, and viral_video_system modules."
