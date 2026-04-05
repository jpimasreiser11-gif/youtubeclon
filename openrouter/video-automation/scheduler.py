from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime, timedelta
import os
import sys

# Import modules
from modules.trending import get_trending
from modules.downloader import download_video
from modules.clipper import create_clips
from modules.ai_generator import generate_video
from modules.uploader import upload_video

# Scheduler configuration
scheduler = BlockingScheduler()

def run_full_workflow():
    """Execute the full automation workflow"""
    print(f"[{datetime.now()}] Starting full workflow...")

    # 1. Get trending content
    trending = get_trending()
    print(f"[{datetime.now()}] Found {len(trending)} trending videos")

    # 2. Download and process videos
    processed_count = 0
    for trend in trending[:2]:  # Limit to 2 videos
        print(f"[{datetime.now()}] Processing: {trend}")
        video_path = download_video(trend)
        if video_path:
            clips = create_clips(video_path)
            for clip in clips:
                upload_video(clip)
            processed_count += 1

    # 3. Generate new AI video every 12 hours
    if datetime.now().hour in [0, 12]:  # At midnight and noon
        print(f"[{datetime.now()}] Generating new AI video...")
        ai_video = generate_video()
        if ai_video:
            upload_video(ai_video)

    print(f"[{datetime.now()}] Workflow completed. Processed {processed_count} videos")

def run_scheduler():
    """Start the scheduler with specified intervals"""
    # Schedule tasks
    scheduler.add_job(
        func=get_trending,
        trigger="interval",
        hours=6,
        id='trending_search',
        name='Search trending content',
        replace_existing=True
    )

    scheduler.add_job(
        func=run_full_workflow,
        trigger="interval",
        hours=8,
        id='full_workflow',
        name='Execute full workflow',
        replace_existing=True
    )

    scheduler.add_job(
        func=generate_video,
        trigger="interval",
        hours=12,
        id='ai_generation',
        name='Generate new AI video',
        replace_existing=True
    )

    print("Scheduler started. Press Ctrl+C to exit.")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler stopped.")

if __name__ == "__main__":
    run_scheduler()