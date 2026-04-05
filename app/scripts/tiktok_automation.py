import os
import sys
import json
import logging
import argparse
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TikTokAuto")

def upload_tiktok(video_path, description, state_file="tiktok_state.json"):
    """
    Sube video a TikTok usando Playwright y persistencia de sesión.
    """
    if not os.path.exists(video_path):
        logger.error(f"Archivo de video no encontrado: {video_path}")
        return False

    with sync_playwright() as p:
        logger.info("Iniciando navegador Playwright...")
        browser = p.chromium.launch(headless=True)
        
        # Intentar cargar estado de sesión (cookies + localStorage)
        if os.path.exists(state_file):
            logger.info(f"Cargando sesión desde {state_file}")
            context = browser.new_context(storage_state=state_file)
        else:
            logger.warning(f"No se encontró {state_file}. Se requerirá login manual en modo HEADED para generar este archivo.")
            context = browser.new_context()

        page = context.new_page()
        
        try:
            logger.info("Navegando a la página de subida de TikTok...")
            page.goto("https://www.tiktok.com/creator-center/upload", wait_until="networkidle")
            
            # Verificar si estamos logueados
            if "login" in page.url.lower():
                logger.error("No se detectó sesión activa. Por favor, genera el state.json primero.")
                browser.close()
                return False

            logger.info("Localizando selector de archivos...")
            # Selector de archivo (input oculto de tipo file)
            file_input = page.wait_for_selector('input[type="file"]')
            file_input.set_input_files(video_path)
            
            logger.info("Subiendo video...")
            # Esperar a que aparezca el campo de descripción (indica que el upload empezó/terminó procesamiento inicial)
            page.wait_for_selector('div[contenteditable="true"]', timeout=60000)
            
            logger.info("Configurando descripción...")
            # Limpiar y escribir descripción
            page.fill('div[contenteditable="true"]', description)
            
            # Pausa para asegurar que los metadatos se procesen
            page.wait_for_timeout(5000)
            
            logger.info("Presionando botón 'Publicar'...")
            # Buscar el botón de post
            post_button = page.get_by_text("Publicar", exact=True)
            if not post_button.is_visible():
                post_button = page.get_by_text("Post", exact=True)
            
            post_button.click()
            
            # Esperar confirmación de éxito
            logger.info("Esperando confirmación de publicación...")
            page.wait_for_selector('text="Publicado"', timeout=60000)
            
            logger.info("✅ ¡Video publicado exitosamente en TikTok!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error durante la subida: {str(e)}")
            # Capturar pantallazo de error para depuración
            page.screenshot(path="tiktok_error_screenshot.png")
            return False
        finally:
            browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automatización de TikTok")
    parser.add_argument("--video", required=True, help="Ruta al video MP4")
    parser.add_argument("--desc", required=True, help="Descripción del video")
    parser.add_argument("--state", default="tiktok_state.json", help="Archivo state.json de Playwright")
    
    args = parser.parse_args()
    
    success = upload_tiktok(args.video, args.desc, args.state)
    sys.exit(0 if success else 1)
