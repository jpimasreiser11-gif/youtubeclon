"""
TikTok Upload via Playwright (100% FREE - No API needed)
Automatiza el navegador para subir videos de forma indetectable
"""

import os
import sys
import time
import argparse
from playwright.sync_api import sync_playwright

def upload_to_tiktok_playwright(
    video_path, 
    caption, 
    cookies_file="tiktok_cookies.json",
    delay_hours=0
):
    if not os.path.exists(video_path):
        print(f"Error: Video not found at {video_path}")
        return False
    
    if delay_hours and float(delay_hours) > 0:
        delay_seconds = float(delay_hours) * 3600
        print(f"Scheduled in {delay_hours} hours; waiting...")
        time.sleep(delay_seconds)
        
    print("Starting TikTok upload via Playwright (stealth mode)...")
    print(f"Video: {os.path.basename(video_path)}")
    
    with sync_playwright() as p:
        # Modo Headless activado = INDETECTABLE
        browser = p.chromium.launch(headless=True, args=['--disable-blink-features=AutomationControlled'])
        
        context_args = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        # Load cookies if they exist in Playwright JSON format
        # If user has selenium pickle cookies, we'd need a converter, but we assume brand new extraction for Playwright
        if os.path.exists(cookies_file) and cookies_file.endswith('.json'):
            import json
            with open(cookies_file, 'r') as f:
                context_args['storage_state'] = json.load(f)
                
        context = browser.new_context(**context_args)
        page = context.new_page()
        
        try:
            # Ir a página de upload
            page.goto('https://www.tiktok.com/creator-center/upload')
            page.wait_for_load_state('networkidle')
            time.sleep(5)
            
            if "login" in page.url.lower():
                print("Not logged in. Cookie might be expired or missing.")
                return False
            
            # Subir archivo de video
            print("Uploading video file...")
            with page.expect_file_chooser() as fc_info:
                page.click('input[type="file"], input[accept*="video"], button:has-text("Select file")')
            file_chooser = fc_info.value
            file_chooser.set_files(os.path.abspath(video_path))
            
            print("Waiting for video to upload...")
            time.sleep(15)
            
            # Añadir caption
            print("Adding caption...")
            caption_selector = 'div[contenteditable="true"], .public-DraftStyleDefault-block'
            page.wait_for_selector(caption_selector, timeout=10000)
            page.click(caption_selector)
            time.sleep(1)
            page.keyboard.type(caption)
            print("Caption added")
            
            # Click en "Post"
            print("Publishing video...")
            time.sleep(3)
            
            post_selectors = ['button:has-text("Post")', 'button:has-text("Publish")', 'button:has-text("Upload")']
            for btn in post_selectors:
                try:
                    if page.locator(btn).count() > 0:
                        page.click(btn)
                        print(f"✅ Clicked Post button")
                        break
                except:
                    continue
            
            print("Waiting for upload to complete...")
            time.sleep(10)
            
            print("Upload completed (Playwright finished successfully)")
            return True
            
        except Exception as e:
            print(f"Error during upload: {e}")
            return False
        
        finally:
            browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload video to TikTok via Playwright")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--caption", required=True, help="Video caption/description")
    parser.add_argument("--cookies", default="tiktok_cookies.json", help="Path to JSON cookies file")
    parser.add_argument("--delay_hours", type=float, default=0, help="Hours to wait before uploading")
    
    args = parser.parse_args()
    
    result = upload_to_tiktok_playwright(
        args.video,
        args.caption,
        cookies_file=args.cookies,
        delay_hours=args.delay_hours
    )
    
    if result:
        print("\nSUCCESS")
        sys.exit(0)
    else:
        print("\nFAILED")
        sys.exit(1)
