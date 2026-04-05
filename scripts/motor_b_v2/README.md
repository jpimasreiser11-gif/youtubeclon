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

Minimum requirements (must-have)
- Python dependencies installed from requirements.txt
- ffmpeg + ffprobe available in PATH

APIs and env vars
- PEXELS_API_KEY (optional, recommended for real footage)
- PIXABAY_API_KEY (optional fallback for real footage)
- MOTOR_B_MUSIC_PATH (optional local soundtrack path)

Setup commands (Windows PowerShell)
- pip install -r requirements.txt
- pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
- ffmpeg -version
- ffprobe -version

Example .env snippet
- PEXELS_API_KEY=your_pexels_key_here
- PIXABAY_API_KEY=your_pixabay_key_here
- MOTOR_B_MUSIC_PATH=C:/Users/you/Music/background.mp3

Optional publishing setup
- youtube_token.json at repository root for automatic upload.
- OAuth scope needed: https://www.googleapis.com/auth/youtube.upload

Notes
- The pipeline is resilient by design: if one dependency is missing, it falls back to a lighter path.
- For highest quality voice, install chatterbox-tts and provide GPU.
- If no footage APIs are configured, the system still works but uses more AI fallback visuals.
