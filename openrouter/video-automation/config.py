import os
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

# OpenRouter API key for Llama model
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# YouTube API credentials
YOUTUBE_CLIENT_SECRET_PATH = os.getenv("YOUTUBE_CLIENT_SECRET_PATH", "client_secret.json")

# Pexels API key for free images
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# Channel niche and settings
CHANNEL_NICHE = os.getenv("CHANNEL_NICHE", "curiosities facts english")
MAX_VIDEOS_PER_DAY = int(os.getenv("MAX_VIDEOS_PER_DAY", "3"))
OUTPUT_LANGUAGE = os.getenv("OUTPUT_LANGUAGE", "english")

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
DOWNLOADS_DIR = os.path.join(OUTPUT_DIR, "downloads")
CLIPS_DIR = os.path.join(OUTPUT_DIR, "clips")
GENERATED_DIR = os.path.join(OUTPUT_DIR, "generated")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# Ensure directories exist
for directory in [OUTPUT_DIR, DOWNLOADS_DIR, CLIPS_DIR, GENERATED_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)