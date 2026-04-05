name: uploader
description: Sube videos renderizados a TikTok/YouTube utilizando automatización de navegador indetectable.

# Uploader Skill

## Cuándo usar
Cuando el video está en estado 'rendered'.

## Gestión de Sesión (Persistencia)
**ADVERTENCIA DE SEGURIDAD:** NUNCA intentes loguearte con usuario/contraseña directamente en el script, ya que disparará captchas imposibles de resolver por el agente.
- **Estrategia**: Usa "Context Hydration".
- Requiere un script previo `src/distribution/auth_capture.py` que el usuario ejecuta UNA VEZ en modo `headless=False` para loguearse manualmente. Este script guarda el estado con `context.storage_state(path="auth/tiktok_state.json")`.

## Flujo de Subida (TikTok)
1. **Verificación**: Comprueba si existe `auth/tiktok_state.json`. Si no, aborta y pide al usuario que autentique.
2. **Inicialización**:
   - Lanza Playwright con `headless=True` (o False si se prefiere depurar).
   - Argumentos Stealth: `--disable-blink-features=AutomationControlled`, User-Agent realista.
   - Carga el contexto: `browser.new_context(storage_state="auth/tiktok_state.json")`.
3. **Navegación**:
   - Ve a `https://www.tiktok.com/upload`.
   - Espera selector de input de archivo.
4. **Acción**:
   - `page.locator('input[type="file"]').set_input_files(path_to_video)`.
   - Espera a que la barra de progreso llegue al 100% o aparezca el texto "Uploaded".
   - Rellena la descripción con el Título + Hashtags generados en el paso de guion.
   - Haz clic en "Post".
5. **Finalización**:
   - Actualiza DB a 'uploaded'.
   - Mueve el archivo a `assets/archived/`.
