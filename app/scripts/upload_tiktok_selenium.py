"""
TikTok Upload via Selenium (100% FREE - No API needed)
Automatiza el navegador para subir videos sin necesitar aprobación de TikTok API
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

def upload_to_tiktok_selenium(
    video_path, 
    caption, 
    cookies_file="tiktok_cookies.txt",
    schedule_time=None,
    delay_hours=0
):
    """
    Sube un video a TikTok usando Selenium (método sin API oficial)
    
    Args:
        video_path: Ruta al archivo de video
        caption: Texto de la descripción/caption
        cookies_file: Archivo con cookies de sesión guardadas
        schedule_time: (Opcional) Fecha/hora para programar (formato: "YYYY-MM-DD HH:MM")
    
    Returns:
        True si tiene éxito
    """
    
    if not os.path.exists(video_path):
        print(f"Error: Video not found at {video_path}")
        return False
    
    if delay_hours and float(delay_hours) > 0:
        delay_seconds = float(delay_hours) * 3600
        print(f"Scheduled in {delay_hours} hours; waiting...")
        time.sleep(delay_seconds)
        
    print("Starting TikTok upload via Selenium...")
    print(f"Video: {os.path.basename(video_path)}")
    print(f"Caption: {caption[:50]}...")
    
    # Configurar Chrome
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Ir a TikTok
        driver.get('https://www.tiktok.com')
        time.sleep(3)
        
        # Cargar cookies
        if os.path.exists(cookies_file):
            print("Loading saved cookies...")
            import pickle
            try:
                with open(cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                    for cookie in cookies:
                        try:
                            driver.add_cookie(cookie)
                        except:
                            pass
                driver.refresh()
                time.sleep(3)
            except:
                print("⚠️ Could not load cookies file")
        else:
            print("No cookies found. Please login manually and save cookies.")
            return False
        
        # Ir a página de upload
        driver.get('https://www.tiktok.com/creator-center/upload')
        time.sleep(5)
        
        # Verificar si estamos logueados
        if "login" in driver.current_url.lower():
            print("❌ Not logged in. Cookie might be expired. Please login manually again.")
            return False
        
        # Subir archivo de video
        print("Uploading video file...")
        
        # Buscar input de archivo (puede tener diferentes selectores)
        file_input_selectors = [
            'input[type="file"]',
            'input[accept*="video"]',
            'input[name="video"]'
        ]
        
        file_input = None
        for selector in file_input_selectors:
            try:
                file_input = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
        
        if not file_input:
            print("❌ Could not find file input")
            return False
        
        file_input.send_keys(os.path.abspath(video_path))
        print("Waiting for video to upload (this may take a while)...")
        time.sleep(15)  # Esperar a que suba
        
        # Añadir caption
        print("Adding caption...")
        time.sleep(5)
        
        caption_selectors = [
            'div[contenteditable="true"]',
            'div[data-placeholder*="caption"]',
            'div[class*="caption"]'
        ]
        
        caption_input = None
        for selector in caption_selectors:
            try:
                caption_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                break
            except:
                continue
        
        if caption_input:
            caption_input.click()
            time.sleep(1)
            caption_input.send_keys(caption)
            print("Caption added")
        else:
            print("Could not find caption input")
        
        # Desmarcar "Allow users to comment" si lo encuentras
        # (Opcional, dependiendo de tu preferencia)
        
        # Programar publicación si se especifica
        if schedule_time:
            print(f"Scheduling for: {schedule_time}")
            try:
                # Buscar opción de programar
                schedule_toggle = driver.find_element(By.XPATH, '//*[contains(text(), "Schedule")]')
                schedule_toggle.click()
                time.sleep(2)
                
                # Aquí tendrías que implementar la lógica de selección de fecha/hora
                # Esto varía según la interfaz de TikTok
                
            except:
                print("⚠️ Could not schedule - posting immediately")
        
        # Click en "Post"
        print("Publishing video...")
        time.sleep(3)
        
        post_button_texts = ['Post', 'Publish', 'Upload', 'Publicar']
        
        for button_text in post_button_texts:
            try:
                post_button = driver.find_element(
                    By.XPATH, 
                    f'//button[contains(text(), "{button_text}")]'
                )
                post_button.click()
                print(f"Clicked '{button_text}' button")
                break
            except:
                continue
        
        print("Waiting for upload to complete...")
        time.sleep(10)
        
        # Verificar si hay mensaje de éxito
        try:
            success_indicators = [
                'Your video is being uploaded',
                'Video uploaded',
                'Successfully',
                'published'
            ]
            
            page_text = driver.page_source.lower()
            
            for indicator in success_indicators:
                if indicator.lower() in page_text:
                    print("Video uploaded successfully to TikTok!")
                    return True
            
            print("Upload completed (check TikTok to confirm)")
            return True
            
        except:
            print("Could not verify upload status")
            print("Check your TikTok profile to confirm upload")
            return True
        
    except Exception as e:
        print(f"Error during upload: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("Cleaning up...")
        time.sleep(3)
        driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload video to TikTok via Selenium")
    parser.add_argument("--video", required=True, help="Path to video file")
    parser.add_argument("--caption", required=True, help="Video caption/description")
    parser.add_argument("--cookies", default="tiktok_cookies.txt", help="Path to cookies file")
    parser.add_argument("--schedule", help="Schedule time (YYYY-MM-DD HH:MM)")
    parser.add_argument("--delay_hours", type=float, default=0, help="Hours to wait before uploading")
    
    args = parser.parse_args()
    
    result = upload_to_tiktok_selenium(
        args.video,
        args.caption,
        cookies_file=args.cookies,
        schedule_time=args.schedule,
        delay_hours=args.delay_hours
    )
    
    if result:
        print("\nSUCCESS")
        sys.exit(0)
    else:
        print("\nFAILED")
        sys.exit(1)
