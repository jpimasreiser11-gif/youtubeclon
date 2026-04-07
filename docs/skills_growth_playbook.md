# Skills Growth Playbook (Copilot + Project)

## Objetivo
Usar skills como aceleradores de ejecucion, no como teoria. Este documento te dice:
1. Que skills ya estan disponibles.
2. Que ya se aplico en el proyecto.
3. Como invocarlos con prompts utiles.

## Skills disponibles en este repo
- product-marketing-context
- pricing-strategy
- page-cro
- analytics-tracking
- launch-strategy
- banana
- notebooklm
- humanizer
- remotion
- webapp-testing

Origen: espejados en `.agents/skills/`.

## Aplicado ya en este proyecto
- Contexto de marketing creado en `.agents/product-marketing-context.md`.
- Plan de tracking creado en `docs/analytics-tracking-plan.md`.
- Roadmap de monetizacion creado en `docs/monetization-roadmap.md`.
- Eventos de analytics instrumentados en:
  - `app/lib/analytics.ts`
  - `app/app/page.tsx`
  - `app/app/motor-b/page.tsx`
  - `app/app/clipradar/page.tsx`

## Como usar cada skill (prompts listos)

### product-marketing-context
Para actualizar ICP, dolor principal o diferenciacion.

Prompt:
"Usa product-marketing-context y actualiza `.agents/product-marketing-context.md` con nuevos ICP y objeciones de agencias."

### pricing-strategy
Para definir planes, limites y metrica de valor.

Prompt:
"Usa pricing-strategy para proponer precios Starter/Pro/Agency con limites por jobs completados al mes y racional de margen."

### page-cro
Para mejorar conversion en home, pricing o onboarding.

Prompt:
"Usa page-cro para optimizar la home: titular, CTA principal, prueba social y fricciones del primer job."

### analytics-tracking
Para ampliar tracking y medir embudo real.

Prompt:
"Usa analytics-tracking para extender eventos de frontend a backend y definir conversiones GA4 para job_completed y paid_upgrade."

### launch-strategy
Para planificar alpha, beta y lanzamiento publico.

Prompt:
"Usa launch-strategy para un plan de 30 dias con canales owned/rented/borrowed y checklist de lanzamiento semanal."

### banana
Para creatividades (thumbnails, banners, ads).

Prompt:
"Usa banana para generar 5 conceptos de thumbnail para nicho misterios y enigmas con CTA visual fuerte."

### notebooklm
Para respuestas con fuentes (docs internos, research).

Prompt:
"Usa notebooklm para responder dudas de posicionamiento con citas a docs de producto y comparativas."

### humanizer
Para pulir copy de ventas o outreach.

Prompt:
"Usa humanizer para reescribir este email de ventas y que suene natural, directo y menos AI."

### remotion
Para plantillas audiovisuales reproducibles.

Prompt:
"Usa remotion para proponer una plantilla vertical 9:16 reutilizable de caso de exito con captions animados."

### webapp-testing
Para smoke tests automáticos antes de release.

Prompt:
"Usa webapp-testing para validar: Home crea Motor A, Motor B crea job, y Projects muestra estado actualizado."

## Regla practica de uso
- Si la tarea es estrategia de negocio: `product-marketing-context` + `pricing-strategy` + `launch-strategy`.
- Si la tarea es conversion: `page-cro` + `analytics-tracking`.
- Si la tarea es contenido creativo: `banana` + `remotion` + `humanizer`.
- Si la tarea es validacion tecnica: `webapp-testing`.
