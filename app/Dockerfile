# EduMind AI Learning Guide - Full Stack Dockerfile
# Next.js + Python video processing

FROM node:20-bookworm AS base

# Install Python and system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create Python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages for video processing
RUN pip install --no-cache-dir \
    yt-dlp \
    moviepy \
    openai-whisper \
    google-generativeai \
    opencv-python-headless \
    pillow \
    numpy \
    psycopg2-binary \
    pyloudnorm \
    mediapipe

# Install Node.js dependencies
COPY package*.json ./
RUN npm ci

# Copy rest of the app
COPY . .

# Build Next.js
RUN npm run build

# Expose port
EXPOSE 3000

# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000

# Start the application
CMD ["npm", "start"]
