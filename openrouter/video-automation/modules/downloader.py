import os
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path

# Import config
from config import DOWNLOADS_DIR

# Initialize logger
logger = logging.getLogger(__name__)

class Downloader:
    def __init__(self):
        self.downloaded_files = self.load_downloaded_files()

    def load_downloaded_files(self):
        """Load the list of already downloaded files"""
        downloaded_file = os.path.join(DOWNLOADS_DIR, "downloaded.json")
        if os.path.exists(downloaded_file):
            try:
                with open(downloaded_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading downloaded files: {e}")
        return []

    def save_downloaded_files(self):
        """Save the list of downloaded files"""
        downloaded_file = os.path.join(DOWNLOADS_DIR, "downloaded.json")
        try:
            with open(downloaded_file, 'w', encoding='utf-8') as f:
                json.dump(self.downloaded_files, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving downloaded files: {e}")

    def get_video_hash(self, url):
        """Generate a hash for the video URL to check duplicates"""
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def is_already_downloaded(self, url):
        """Check if video is already downloaded"""
        video_hash = self.get_video_hash(url)
        return video_hash in self.downloaded_files

    def mark_as_downloaded(self, url):
        """Mark video as downloaded"""
        video_hash = self.get_video_hash(url)
        self.downloaded_files.append(video_hash)
        self.save_downloaded_files()

    def download_video(self, url):
        """Download video from YouTube"""
        if self.is_already_downloaded(url):
            logger.info(f"Video already downloaded: {url}")
            return None

        from yt_dlp import YoutubeDL

        # Create download directory
        Path(DOWNLOADS_DIR).mkdir(parents=True, exist_ok=True)

        # Generate safe filename
        filename = f"video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
        filepath = os.path.join(DOWNLOADS_DIR, filename)

        # Download options
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best[height<=1080]',  # Limit to 1080p to save space
            'outtmpl': filepath,
            'restrictfilenames': True
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            logger.info(f"Downloaded video: {filename}")
            self.mark_as_downloaded(url)
            return filepath
        except Exception as e:
            logger.error(f"Error downloading video: {e}")
            return None

# Create global instance
downloader = Downloader()

def download_video(url):
    """Public function to download video"""
    return downloader.download_video(url)