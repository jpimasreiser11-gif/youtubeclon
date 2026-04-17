# Free Documentary Stack Research (applied to current pipeline)

## Objective
Improve documentary quality with free tools, reduce repeated visuals, and keep the pipeline stable at $0 base cost.

## Verified sources
1. **FFmpeg Filters Documentation**  
   https://ffmpeg.org/ffmpeg-filters.html  
   Key value: advanced filters for motion, color grading, denoise, subtitles, audio mixing.

2. **OpenAI Whisper (GitHub)**  
   https://github.com/openai/whisper  
   Key value: local speech-to-text/subtitles, multilingual support, ffmpeg integration.

3. **Pixabay API Docs**  
   https://pixabay.com/api/docs/  
   Key value: free videos/images API, JSON REST, clear rate limits, proper caching rules.

4. **edge-tts (GitHub)**  
   https://github.com/rany2/edge-tts  
   Key value: free neural TTS, configurable voice/rate/pitch/volume, subtitle output support.

5. **MediaWiki Action API**  
   https://www.mediawiki.org/wiki/API:Main_page  
   Key value: free API endpoint model (`/w/api.php`) used for Wikimedia fallback assets.

## Notes on source access
- Pexels docs page blocked for automated fetch during this session (HTTP 403).  
  URL to verify manually in browser: https://www.pexels.com/api/documentation/

## Improvements implemented in this codebase
### 1) Visual diversity / anti-repetition
- Added usage ledger per channel in `backend/pipeline/video_builder.py`:
  - stores previously used asset URLs,
  - stores file fingerprints (hashes),
  - skips reused URLs and duplicate clips.
- Applied same deduplication to Wikimedia fallback clips.

### 2) Voice quality cleanup
- Expanded text normalization in `backend/pipeline/voice_generator.py`:
  - strips problematic quotes/typographic symbols,
  - removes markdown links/URLs/emails from narration text,
  - normalizes punctuation spacing for cleaner prosody.

### 3) Full reset / delete video flow
- New API routes in `backend/routes/videos.py`:
  - `DELETE /api/videos/{video_id}`
  - `DELETE /api/videos/purge/all`
- New DB helpers in `backend/database.py`:
  - `delete_video(video_id)`
  - `delete_all_videos()`
- UI actions in `frontend/src/pages/Library.jsx` + `frontend/src/api.js`:
  - per-video delete button,
  - “delete all videos” button.

## Free-first quality profile (recommended)
- Script provider: `local` (avoid external LLM quota failures).
- TTS primary: `edge` (free neural voices).
- Stock footage: Pixabay/Pexels if available, otherwise Wikimedia fallback.
- Subtitles: Whisper local when enabled + embedded burn-in for delivery consistency.

## Practical next refinements (still free)
1. Add scene-level shot type rotation (wide/medium/close) in montage logic.
2. Add loudness normalization (`loudnorm`) pass in final audio chain.
3. Add hard no-repeat window across last N videos per channel in DB table (not only file ledger).
