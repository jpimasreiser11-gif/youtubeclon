---
name: trend-hunter
description: Habilidad para identificar nichos virales.
---
# Cazador de Tendencias

## Objetivo
Generar 5 ideas de video virales diarias basadas en análisis de tendencias.

## Instrucciones
1. Usa la herramienta de navegador para escanear 'Google Trends' y 'TikTok Creative Center'.
2. Filtra temas que tengan alto potencial visual y engagement reciente.
3. Genera un JSON con la siguiente estructura:
   - 'nicho': El tema principal.
   - 'gancho': Frase impactante para los primeros 3 segundos.
   - 'palabras_clave_visuales': Términos para buscar en Pexels.
4. Valida que los temas no sean repetidos (consulta la base de datos si es posible).
