# Flujo Viral Pro

Sistema autónomo de generación de videos virales.

## Configuración
1.  **Entorno Virtual**:
    `ash
    python -m venv venv
    .\venv\Scripts\Activate
    pip install -r requirements.txt
    playwright install
    `

2.  **Credenciales**:
    -   Configura GEMINI_API_KEY y PEXELS_API_KEY como variables de entorno.
    -   Configura el acceso a Google Sheets (MCP) si deseas persistencia.

3.  **Ejecución**:
    `ash
    python main.py
    `

## Estructura
-   scripts/: Scripts individuales para cada etapa (TTS, Fetch, Render).
-   .agent/skills/: Definiciones de habilidades agénticas.
-   	emp/: Archivos temporales generados.
