import os
import json
import logging
from datetime import datetime, timedelta
from pytrends.request import TrendReq

# Initialize logger
logger = logging.getLogger(__name__)

class Trending:
    def __init__(self):
        self.pytrends = TrendReq()
        self.trending_cache = {}
        self.cache_duration = timedelta(hours=6)

    def get_trending_keywords(self):
        """Get trending keywords from Google Trends"""
        try:
            # Trending searches
            trending_searches = self.pytrends.trending_searches(pn='p1')  # p1 = worldwide
            keywords = trending_searches['title'].tolist()
            logger.info(f"Found {len(keywords)} trending keywords")
            return keywords
        except Exception as e:
            logger.error(f"Error getting trending keywords: {e}")
            return []

    def search_youtube_videos(self, keywords):
        """Search for YouTube videos related to keywords"""
        from yt_dlp import YoutubeDL
        video_urls = []

        for keyword in keywords[:5]:  # Limit to 5 keywords
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                    'format': 'best',
                    'max_downloads': 3
                }

                with YoutubeDL(ydl_opts) as ydl:
                    results = ydl.extract_info(f"ytsearch:{keyword} curiosities facts science technology", download=False)
                    for entry in results['entries'][:2]:  # Limit to 2 videos per keyword
                        video_urls.append(entry['webpage_url'])
            except Exception as e:
                logger.error(f"Error searching YouTube for {keyword}: {e}")

        return video_urls

    def get_trending_videos(self):
        """Get trending videos with caching"""
        current_time = datetime.now()

        # Check cache
        if 'trending' in self.trending_cache:
            cached_time, cached_videos = self.trending_cache['trending']
            if current_time - cached_time < self.cache_duration:
                logger.info("Using cached trending videos")
                return cached_videos

        # Get fresh data
        keywords = self.get_trending_keywords()
        if not keywords:
            return []

        videos = self.search_youtube_videos(keywords)

        # Cache results
        self.trending_cache['trending'] = (current_time, videos)

        logger.info(f"Found {len(videos)} trending videos")
        return videos

# Create global instance
trending = Trending()

def get_trending():
    """Public function to get trending videos"""
    return trending.get_trending_videos()