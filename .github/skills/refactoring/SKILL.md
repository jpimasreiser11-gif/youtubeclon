---
name: refactoring
description: Refactor seguro para mejorar legibilidad, mantenimiento y robustez sin cambiar comportamiento esperado.
---

Aplicación:
1. Cambios pequeños, reversibles y con foco en claridad.
2. Sin introducir `any` o atajos que rompan type-safety.
3. Conservar contratos públicos y rutas API existentes.
