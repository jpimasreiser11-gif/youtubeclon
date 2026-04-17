# video-pipeline-expert

Use when working on any pipeline module:
`trend_finder`, `script_writer`, `voice_generator`, `video_builder`, `thumbnail_creator`, `metadata_writer`, `publisher`, `orchestrator`.

## Architecture references
- Shared state: SQLite (`videos`, `trends`, `pipeline_logs`, `channels`).
- Main orchestrator: `backend/pipeline/orchestrator.py`.
- Fallback behavior: seed topics, retries, provider fallback.

## Module contracts
- trend_finder -> topic + score
- script_writer -> title + script + broll_markers
- voice_generator -> audio_path + duration
- video_builder -> video_path
- metadata_writer -> title/description/tags
- publisher -> youtube_url or explicit error

## Engineering rules
- Log every step in `pipeline_logs`.
- Never swallow errors silently.
- Keep data contracts stable and explicit.
- Prefer deterministic fallback over random fallback.

## Testing strategy
- Unit tests per module output shape.
- Integration test for single-channel pipeline.
- Parallel test for multi-channel orchestration.

