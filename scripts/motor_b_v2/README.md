Motor B v2 (English Mystery Stack)

What this package provides
- English script generation optimized for mystery/paranormal short videos.
- Real footage fetch from Pexels/Pixabay with AI-image fallback.
- Cinematic voice generation (Chatterbox preferred, Edge-TTS fallback).
- Documentary style ASS subtitles.
- End-to-end assembly and optional YouTube publishing.

Quick run
- python scripts/motor_b_v2/main_en.py
- python scripts/motor_b_v2/main_en.py "The Dyatlov Pass Incident" mystery 65

Required env vars
- PEXELS_API_KEY (optional but recommended)
- PIXABAY_API_KEY (optional)
- MOTOR_B_MUSIC_PATH (optional local soundtrack)

Optional publishing setup
- youtube_token.json at repository root for automatic upload.

Notes
- The pipeline is resilient by design: if one dependency is missing, it falls back to a lighter path.
- For highest quality voice, install chatterbox-tts and provide GPU.
