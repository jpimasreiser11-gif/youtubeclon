import os
import sys
import time
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def upload_to_tiktok_selenium(video_path, caption, cookies_path='tiktok_cookies.txt'):
    """
    Sube un video a TikTok usando Selenium (método no oficial)
    
    Args:
        video_path: Ruta al video
        caption: Descripción/caption del video
        cookies_path: Ruta al archivo de cookies de sesión
    
    IMPORTANTE: Este método requiere cookies de sesión válidas
    """
    
    if not os.path.exists(video_path):
        print(f"Error: Video not found at {video_path}")
        return False
    
    print(f"Starting TikTok upload: {caption[:50]}...")
    
    # Configurar Chrome en modo headless
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Ir a TikTok Creator Studio
        driver.get('https://www.tiktok.com/creator-center/upload')
        
        # Cargar cookies de sesión
        if os.path.exists(cookies_path):
            with open(cookies_path, 'r') as f:
                sessionid = f.read().strip()
                driver.add_cookie({
                    'name': 'sessionid',
                    'value': sessionid,
                    'domain': '.tiktok.com'
                })
            
            # Recargar con cookies
            driver.refresh()
            time.sleep(3)
        else:
            print("Warning: No cookies file found. Upload may fail.")
        
        # Subir video
        upload_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
        )
        upload_input.send_keys(os.path.abspath(video_path))
        
        print("Video file selected, uploading...")
        time.sleep(10)  # Esperar a que suba
        
        # Añadir caption
        caption_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[contenteditable="true"]'))
        )
        caption_box.send_keys(caption)
        
        # Click en "Post"
        post_button = driver.find_element(By.XPATH, '//button[contains(text(), "Post")]')
        post_button.click()
        
        print("Video posted to TikTok successfully!")
        time.sleep(5)
        
        return True
        
    except Exception as e:
        print(f"Error uploading to TikTok: {e}")
        return False
    
    finally:
        driver.quit()

def upload_to_tiktok_api(video_path, caption, access_token):
    """
    Sube a TikTok usando la API oficial (requiere aprobación de TikTok)
    
    NOTA: Este método requiere:
    1. Aplicación aprobada por TikTok
    2. Access token válido
    3. Permisos de Content Posting API
    """
    
    import requests
    
    url = "https://open-api.tiktok.com/share/video/upload/"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "multipart/form-data"
    }
    
    with open(video_path, 'rb') as video_file:
        files = {'video': video_file}
        data = {
            'caption': caption,
            'privacy_level': 'PUBLIC_TO_EVERYONE'
        }
        
        response = requests.post(url, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            print("Video uploaded to TikTok via API")
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload video to TikTok")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--caption", required=True, help="Video caption")
    parser.add_argument("--method", default="selenium", choices=['selenium', 'api'])
    parser.add_argument("--cookies", default="tiktok_cookies.txt", help="Path to cookies file (for Selenium)")
    parser.add_argument("--token", help="Access token (for API method)")
    
    args = parser.parse_args()
    
    if args.method == 'selenium':
        upload_to_tiktok_selenium(args.video, args.caption, args.cookies)
    else:
        if not args.token:
            print("Error: --token required for API method")
            sys.exit(1)
        upload_to_tiktok_api(args.video, args.caption, args.token)
