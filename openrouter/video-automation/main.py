import os
import sys
from datetime import datetime
from modules.scheduler import Scheduler
from modules.trending import get_trending
from modules.downloader import download_video
from modules.clipper import create_clips
from modules.ai_generator import generate_video
from modules.uploader import upload_video
from modules.stats import get_stats

# Main menu
while True:
    print("\nVideo Automation System")
    print("1. Run all tasks now")
    print("2. Start scheduler (24/7)")
    print("3. Process specific URL")
    print("4. Generate new AI video")
    print("5. View statistics")
    print("6. Exit")
    choice = input("Select option (1-6): ")

    if choice == '1':
        # Run all tasks now
        trending = get_trending()
        for trend in trending:
            video = download_video(trend)
            clips = create_clips(video)
            for clip in clips:
                upload_video(clip)
        print("All tasks completed successfully")
    elif choice == '2':
        # Start scheduler
        scheduler = Scheduler()
        scheduler.start()
        print("Scheduler started. Press Ctrl+C to stop")
        scheduler.join()
    elif choice == '3':
        # Process specific URL
        url = input("Enter YouTube URL: ")
        download_video(url)
        clips = create_clips(url)
        for clip in clips:
            upload_video(clip)
        print("Processing completed")
    elif choice == '4':
        # Generate new AI video
        generate_video()
        print("AI video generated")
    elif choice == '5':
        # View statistics
        stats = get_stats()
        print(f"Total videos processed: {stats['total_processed']}")
        print(f"Total clips generated: {stats['total_clips']}")
        print(f"Total videos uploaded: {stats['total_uploaded']}")
    elif choice == '6':
        print("Exiting system")
        sys.exit()
    else:
        print("Invalid choice. Please select 1-6