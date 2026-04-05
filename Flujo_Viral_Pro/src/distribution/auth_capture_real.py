from playwright.sync_api import sync_playwright
import os
import shutil
import time

def capture_auth_real_profile():
    print("=== TikTok Auth Capture Tool (REAL PROFILE) ===")
    print("!!! ADVERTENCIA: DEBES CERRAR GOOGLE CHROME COMPLETAMENTE ANTES DE SEGUIR !!!")
    print("Si Chrome está abierto, este script fallará inmediatamente.")
    print("------------------------------------------------------------------")
    print("Presiona ENTER solo cuando hayas CERRADO todas las ventanas de Chrome.")
    input()

    # User Data Path
    user_data_dir = os.path.join(os.environ["LOCALAPPDATA"], "Google", "Chrome", "User Data")
    
    # Check if exists
    if not os.path.exists(user_data_dir):
        print(f"No se encontró Chrome en: {user_data_dir}")
        return

    # Output path
    auth_dir = "auth"
    os.makedirs(auth_dir, exist_ok=True)
    auth_path = os.path.join(auth_dir, "tiktok_state.json")

    with sync_playwright() as p:
        print("\nLanzando tu Chrome con tu perfil real...")
        try:
            # Launch persistent context
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"] # Anti-bot
            )
            
            page = context.new_page()
            
            print("\nAbriendo TikTok Login...")
            try:
                page.goto("https://www.tiktok.com/@") # Go to profile directly if possible
            except Exception as e:
                print(f"Error loading page: {e}")

            print("\n--> Si ya estás logueado, verás tu perfil.")
            print("--> Si no, logueate ahora.")
            print("--> EL SCRIPT GUARDARÁ LA SESIÓN AUTOMÁTICAMENTE CADA 5 SEGUNDOS.")
            print("--> CUANDO TERMINES, SIMPLEMENTE CIERRA EL NAVEGADOR.")
            
            while True:
                try:
                    # Check if browser is still open by checking pages
                    if not context.pages:
                        print("Navegador cerrado. Finalizando.")
                        break
                        
                    context.storage_state(path=auth_path)
                    print(f"Sesión actualizada en {auth_path}...")
                    time.sleep(5)
                except Exception as e:
                    print(f"Detectado cierre de navegador ({e}).")
                    break
            
            try:
                context.close()
            except:
                pass
            
        except Exception as e:
            print("\n❌ ERROR CRÍTICO:")
            print(f"{e}")
            print("\nPosible causa: Chrome seguía abierto en segundo plano.")
            print("Intenta cerrar Chrome desde el Administrador de Tareas.")

if __name__ == "__main__":
    capture_auth_real_profile()
