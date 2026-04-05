---
name: content-database
description: Habilidad para gestionar persistencia de datos en Google Sheets.
---
# Gestor de Base de Datos

## Objetivo
Gestionar el estado de los videos en Google Sheets a través de MCP.

## Instrucciones
1. Conéctate a la hoja 'Pipeline_Viral' usando el servidor MCP.
2. Función guardar_ideas: Añade nuevas filas con fecha, nicho, guion y estado 'Pendiente'.
3. Función obtener_pendientes: Lee filas donde Estado = 'Pendiente' para procesar.
4. Función actualizar_estado: Cambia el estado (ej. de 'Pendiente' a 'Guionizado', 'Renderizado', 'Subido') y añade la ruta local del archivo MP4 cuando corresponda.
