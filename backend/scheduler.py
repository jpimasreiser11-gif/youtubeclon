"""
YouTube Automation Pro — APScheduler Integration
Monitors the `schedule` table and automatically uploads processed videos.
"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor

from .database import get_db, dicts_from_rows, update_video, get_video
from .pipeline.youtube_publisher import upload_video_to_youtube

logger = logging.getLogger("youtube-auto-pro.scheduler")

# Create a scheduler with a robust thread pool (since uploads block heavily)
executors = {
    'default': ThreadPoolExecutor(3)
}
_scheduler = BackgroundScheduler(executors=executors)


def check_and_publish_videos():
    """Timer job that scans the SQLite database for videos meeting schedule criteria."""
    now_iso = datetime.now().isoformat()
    
    query = """
        SELECT s.id as schedule_id, s.channel_id, s.video_id, s.scheduled_at 
        FROM schedule s
        JOIN videos v ON s.video_id = v.id
        WHERE s.status = 'pending'
          AND s.scheduled_at <= ?
          AND v.status IN ('ready', 'video_ready', 'thumbnail_ready')
    """
    
    with get_db() as conn:
        rows = conn.execute(query, (now_iso,)).fetchall()
        jobs = dicts_from_rows(rows)
        
    for job in jobs:
        schedule_id = job["schedule_id"]
        channel_id = job["channel_id"]
        video_id = job["video_id"]
        
        logger.info(f"Triggering upload for scheduled video {video_id} (Channel {channel_id})")
        
        # Mark schedule as processing to avoid duplicate triggers
        with get_db() as conn:
            conn.execute("UPDATE schedule SET status = 'processing' WHERE id = ?", (schedule_id,))
            
        video_data = get_video(video_id)
        if not video_data:
            with get_db() as conn:
                conn.execute("UPDATE schedule SET status = 'error' WHERE id = ?", (schedule_id,))
            continue
            
        # Re-attach slugs for publisher if needed (get_video doesn't auto-join)
        # But we added fallback logic in the publisher, so it's fine.
        
        # Perform upload synchronously within the threaded executor
        success = upload_video_to_youtube(video_data, channel_id)
        
        with get_db() as conn:
            if success:
                conn.execute("UPDATE schedule SET status = 'completed' WHERE id = ?", (schedule_id,))
            else:
                conn.execute("UPDATE schedule SET status = 'error' WHERE id = ?", (schedule_id,))


def start_scheduler():
    """Start the APScheduler ticking."""
    # Run check every 2 minutes
    _scheduler.add_job(check_and_publish_videos, 'interval', minutes=2, id="video_publisher_job", replace_existing=True)
    _scheduler.start()
    logger.info("APScheduler started: Monitoring publish queue every 2 minutes.")


def stop_scheduler():
    """Cleanly shutdown the scheduler."""
    _scheduler.shutdown(wait=False)
    logger.info("APScheduler shutdown.")

if __name__ == "__main__":
    import time
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    start_scheduler()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_scheduler()

