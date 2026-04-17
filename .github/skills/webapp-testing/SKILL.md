---
name: webapp-testing
description: Estrategia de pruebas smoke e integración para backend FastAPI + frontend Vite.
---

Cuando se toque flujo crítico:
1. Ejecuta tests existentes (`pytest` smoke/API).
2. Verifica build frontend.
3. Comprueba endpoints clave del pipeline antes de cerrar tarea.
