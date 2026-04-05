"""
YouTube Upload via Selenium (100% FREE - No API needed)
Automatiza el navegador para subir videos sin usar YouTube Data API
"""

import os
import sys
import time
import argparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

def upload_to_youtube_selenium(
    video_path, 
    title, 
    description="", 
    privacy="unlisted",
    tags=None,
    cookies_file="youtube_cookies.txt",
    delay_hours=0
):
    """
    Sube un video a YouTube usando Selenium (método sin API)
    
    Args:
        video_path: Ruta al archivo de video
        title: Título del video
        description: Descripción del video
        privacy: 'public', 'unlisted', o 'private'
        tags: Lista de tags
        cookies_file: Archivo con cookies de sesión guardadas
    
    Returns:
        URL del video si tiene éxito
    """
    
    if not os.path.exists(video_path):
        print(f"Error: Video not found at {video_path}")
        return None
    
    if delay_hours and float(delay_hours) > 0:
        delay_seconds = float(delay_hours) * 3600
        print(f"Scheduled in {delay_hours} hours; waiting...")
        time.sleep(delay_seconds)
        
    print("Starting YouTube upload via Selenium...")
    print(f"Video: {os.path.basename(video_path)}")
    print(f"Title: {title}")
    
    # Configurar Chrome
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # User agent real
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Ir a YouTube Studio
        driver.get('https://studio.youtube.com')
        time.sleep(3)
        
        # Cargar cookies si existen (para evitar login manual)
        if os.path.exists(cookies_file):
            print("Loading saved cookies...")
            import pickle
            with open(cookies_file, 'rb') as f:
                cookies = pickle.load(f)
                for cookie in cookies:
                    driver.add_cookie(cookie)
            driver.refresh()
            time.sleep(3)
        else:
            print("No cookies found. You'll need to login manually at least once.")
            print("Run this script manually once to save cookies or use the dashboard.")
            return None
        
        # Ir a página de upload
        driver.get('https://www.youtube.com/upload')
        time.sleep(3)
        
        # Seleccionar archivo
        print("Uploading video file...")
        file_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="file"]'))
        )
        file_input.send_keys(os.path.abspath(video_path))
        
        time.sleep(5)
        
        # Añadir título
        print("Setting title...")
        title_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[aria-label*="title"]'))
        )
        title_input.clear()
        time.sleep(1)
        title_input.send_keys(title)
        
        # Añadir descripción si existe
        if description:
            print("Setting description...")
            try:
                desc_input = driver.find_element(By.CSS_SELECTOR, '[aria-label*="description"]')
                desc_input.clear()
                desc_input.send_keys(description)
            except:
                print("Could not set description")
        
        # Click en "No, it's not made for kids"
        print("Setting 'Not made for kids' option...")
        time.sleep(2)
        try:
            not_for_kids = driver.find_element(By.NAME, 'VIDEO_MADE_FOR_KIDS_NOT_MFK')
            not_for_kids.click()
        except:
            print("Could not set made for kids option")
        
        # Click en "Next" (3 veces - detalles, elementos, visibilidad)
        for i in range(3):
            print(f"Clicking Next ({i+1}/3)...")
            time.sleep(2)
            try:
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//ytcp-button[@id="next-button"]'))
                )
                next_button.click()
            except:
                print(f"Could not click next button {i+1}")
        
        # Establecer privacidad
        print(f"Setting privacy to: {privacy}")
        time.sleep(3)
        
        privacy_map = {
            'public': 'PUBLIC',
            'unlisted': 'UNLISTED', 
            'private': 'PRIVATE'
        }
        
        try:
            privacy_radio = driver.find_element(
                By.NAME, 
                f'privacy-radios-group_{privacy_map.get(privacy, "UNLISTED")}'
            )
            privacy_radio.click()
        except:
            print("Could not set privacy, defaulting to unlisted")
        
        # Click en "Publish"
        print("Publishing video...")
        time.sleep(2)
        publish_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//ytcp-button[@id="done-button"]'))
        )
        publish_button.click()
        
        # Esperar a que aparezca el link del video
        print("Waiting for video URL...")
        time.sleep(10)
        
        try:
            video_url_element = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[href^="/watch"]'))
            )
            video_url = "https://www.youtube.com" + video_url_element.get_attribute('href')
            
            print("Video uploaded successfully!")
            print(f"URL: {video_url}")
            
            return video_url
            
        except:
            print("Could not get video URL, but upload likely succeeded")
            print("Check your YouTube Studio: https://studio.youtube.com/")
            return "Upload completed - check YouTube Studio"
        
    except Exception as e:
        print(f"Error during upload: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    finally:
        print("Cleaning up...")
        time.sleep(3)
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload video to YouTube via Selenium")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--privacy", default="unlisted", choices=['public', 'unlisted', 'private'])
    parser.add_argument("--cookies", default="youtube_cookies.txt", help="Path to cookies file")
    parser.add_argument("--delay_hours", type=float, default=0, help="Hours to wait before uploading")
    
    args = parser.parse_args()
    
    result = upload_to_youtube_selenium(
        args.video,
        args.title,
        args.description,
        args.privacy,
        cookies_file=args.cookies,
        delay_hours=args.delay_hours
    )
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)
