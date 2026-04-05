"""
TikTok Upload with Fallback Pattern
Tries fast API method first, falls back to Selenium on failure
"""
import sys
import logging
import json
import psycopg2
import argparse
import os
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def upload_via_api(video_path: str, title: str, hashtags: list) -> dict:
    """
    Fast upload using TikTok API (requests library)
    WARNING: Fragile, breaks when TikTok updates API
    """
    try:
        # Import only if trying this method to avoid dependency issues
        from TiktokAutoUploader import upload_tiktok_video
        
        logger.info("Attempting fast API upload...")
        
        result = upload_tiktok_video(
            video_path=video_path,
            title=title,
            hashtags=hashtags,
            # Add any other params from lib docs
        )
        
        logger.info("API upload successful!")
        return {
            'success': True,
            'method': 'api',
            'result': result
        }
    
    except ImportError:
        logger.warning("TiktokAutoUploader not installed, skipping API method")
        raise Exception("API method not available")
    
    except Exception as e:
        logger.error(f"API upload failed: {str(e)}")
        raise

def upload_via_selenium(video_path: str, title: str, hashtags: list, cookies_path: str = None, user_id: str = None, db_config: dict = None) -> dict:
    """
    Robust upload using browser automation (Selenium)
    """
    try:
        logger.info("Falling back to Selenium upload...")
        
        from tiktok_uploader.upload import upload_video
        from tiktok_uploader.auth import AuthBackend
        
        active_cookies = cookies_path
        tmp_cookies = None
        
        # If user_id provided, fetch cookies from DB
        if user_id and db_config:
            logger.info(f"Fetching cookies for user {user_id} from database...")
            try:
                conn = psycopg2.connect(**db_config)
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT credentials_data FROM platform_credentials 
                    WHERE user_id = %s AND platform = 'tiktok' AND is_active = true
                """, (user_id,))
                row = cursor.fetchone()
                if row:
                    cookies_content = row[0].get('cookies')
                    if cookies_content:
                        # Save to a temporary file because tiktok-uploader expects a path
                        tmp_cookies = f"tiktok_cookies_{user_id}.txt"
                        with open(tmp_cookies, 'w', encoding='utf-8') as f:
                            f.write(cookies_content)
                        active_cookies = tmp_cookies
                        logger.info("Cookies loaded from database")
                cursor.close()
                conn.close()
            except Exception as db_e:
                logger.warning(f"Error fetching cookies from DB: {db_e}")

        # Use cookies if available to skip login
        auth = AuthBackend(cookies=active_cookies) if active_cookies else None
        
        result = upload_video(
            video_path,
            description=f"{title} {' '.join(hashtags)}",
            auth=auth,
            headless=True
        )
        
        # Clean up tmp file
        if tmp_cookies and os.path.exists(tmp_cookies):
            os.remove(tmp_cookies)

        logger.info("Selenium upload successful!")
        return {
            'success': True,
            'method': 'selenium',
            'result': result
        }
    
    except ImportError:
        logger.error("tiktok-uploader not installed")
        raise Exception("Selenium method not available - install tiktok-uploader")
    
    except Exception as e:
        logger.error(f"Selenium upload failed: {str(e)}")
        raise

def upload_with_fallback(
    video_path: str,
    title: str,
    hashtags: list,
    cookies_path: str = None,
    user_id: str = None,
    db_config: dict = None
) -> dict:
    """
    Main upload function with automatic fallback
    
    Args:
        video_path: Path to MP4 file
        title: Video title
        hashtags: List of hashtags (with or without #)
        cookies_path: Optional path to cookies file for Selenium
    
    Returns:
        dict with success status, method used, and result
    """
    # Validate inputs
    if not Path(video_path).exists():
        return {
            'success': False,
            'error': f'Video file not found: {video_path}'
        }
    
    # Normalize hashtags
    hashtags = [f"#{tag.lstrip('#')}" for tag in hashtags]
    
    # Strategy 1: Try API (fast)
    api_error = None
    try:
        return upload_via_api(video_path, title, hashtags)
    except Exception as e:
        api_error = e
        logger.warning(f"API method failed: {api_error}")
    
    # Strategy 2: Fallback to Selenium (slow but reliable)
    try:
        return upload_via_selenium(video_path, title, hashtags, cookies_path, user_id, db_config)
    except Exception as selenium_error:
        logger.error(f"Both methods failed!")
        return {
            'success': False,
            'api_error': str(api_error),
            'selenium_error': str(selenium_error)
        }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Upload video to TikTok")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("title", help="Video title")
    parser.add_argument("--tags", default="", help="Space separated hashtags")
    parser.add_argument("--cookies", help="Path to cookies file")
    parser.add_argument("--user-id", help="User UUID for DB lookup")
    parser.add_argument("--db-host", default="localhost")
    parser.add_argument("--db-name", default="antigravity")
    parser.add_argument("--db-user", default="n8n")
    parser.add_argument("--db-password", default="n8n")
    
    args = parser.parse_args()
    
    db_config = {
        'host': args.db_host,
        'database': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }
    
    hashtags = args.tags.split()
    
    result = upload_with_fallback(
        args.video, 
        args.title, 
        hashtags, 
        cookies_path=args.cookies,
        user_id=args.user_id,
        db_config=db_config
    )
    
    print(f"\nResult: {json.dumps(result)}")
    
    sys.exit(0 if result.get('success') else 1)
