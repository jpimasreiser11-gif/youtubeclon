FROM n8nio/n8n:latest

USER root

# Install system dependencies
RUN apk add --no-cache \
    ffmpeg \
    python3 \
    py3-pip \
    imagemagick \
    font-noto \
    git

# Set up Python environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages
RUN pip install --no-cache-dir \
    yt-dlp \
    openai-whisper \
    moviepy \
    google-generativeai \
    opencv-python-headless \
    pillow

USER node
