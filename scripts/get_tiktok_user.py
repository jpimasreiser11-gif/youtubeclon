import os
import sys
import time
import pickle
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_tiktok_username(session_id):
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        driver.get('https://www.tiktok.com')
        # Add cookie
        driver.add_cookie({
            'name': 'sessionid',
            'value': session_id,
            'domain': '.tiktok.com',
            'path': '/',
            'secure': True,
            'httpOnly': True
        })
        
        # Refresh to apply cookie
        driver.refresh()
        time.sleep(5)
        
        # Check if logged in and get username
        # Try to find user profile info
        driver.get('https://www.tiktok.com/creator-center/upload')
        time.sleep(5)
        
        if "login" in driver.current_url:
            return None, "Login failed - sessionid invalid or expired"
            
        # Try to find username in the page
        try:
            # Common selector for username in creator center
            user_element = driver.find_element(By.CSS_SELECTOR, '[data-tt="user-info-name"], .user-info-name, [class*="Username"]')
            username = user_element.text.strip()
            if username:
                return username, None
        except:
            pass
            
        # Fallback: check profile page
        driver.get('https://www.tiktok.com/profile')
        time.sleep(5)
        try:
            # Selector for unique handle
            handle_element = driver.find_element(By.CSS_SELECTOR, '[data-e2e="user-title"]')
            username = handle_element.text.strip()
            if username:
                return username, None
        except:
            pass
            
        return "TikTok User", "Could not extract specific username but login succeeded"
        
    except Exception as e:
        return None, str(e)
    finally:
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessionid", required=True)
    args = parser.parse_args()
    
    username, error = get_tiktok_username(args.sessionid)
    if username:
        print(f"USERNAME:{username}")
        sys.exit(0)
    else:
        print(f"ERROR:{error}")
        sys.exit(1)
