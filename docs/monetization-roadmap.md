# Monetization Roadmap (Aplicado con Skills)

Last updated: 2026-04-07

## Packaging y Pricing (pricing-strategy)

## Planes propuestos
- Starter
  - Motor A incluido
  - Limite mensual de jobs
  - Sin prioridad de cola
- Pro
  - Motor A + Motor B
  - Limites mayores
  - Prioridad media + exportes avanzados
- Agency
  - Multi-cuenta / multi-cliente
  - Prioridad alta en cola
  - Soporte prioritario + reporting

## Value metric recomendado
- Primario: jobs completados por mes
- Secundario: minutos procesados o creditos de render

Razon: escala con valor real percibido y es facil de entender.

## Go-To-Market por fases (launch-strategy)
1. Alpha cerrada: 10-20 usuarios activos con feedback semanal.
2. Beta con waitlist: mostrar casos reales por nicho (A/B).
3. Early access pagado: onboarding guiado + pricing de entrada.
4. Public launch: apertura self-serve + contenido de prueba social.

## CRO de paginas clave (page-cro)
- Hero: dejar claro en 5 segundos la diferencia Motor A vs Motor B.
- CTA principal unica por pagina (evitar multiples conflictos).
- Prueba social cerca del CTA (casos y resultados).
- Reducir friccion de primer valor: primer job < 10 minutos.

## Funnel y medicion (analytics-tracking)
- North Star: jobs completados/usuario/semana.
- KPI monetizacion:
  - Conversion signup -> job created
  - job created -> completed
  - completed -> paid
  - ARPU y retencion 30 dias

## Quick wins tecnicos (prioridad 14 dias)
1. Implementar cuotas por plan (Starter/Pro/Agency).
2. Prioridad de cola por plan en worker.
3. Mostrar consumo de creditos en UI.
4. Activar pagina de precios con comparativa clara.

## Riesgos a vigilar
- Fijar precio por debajo del valor (alto uso, bajo margen).
- Ofrecer Motor B en plan demasiado barato sin limites.
- No medir calidad de salida por nicho (afecta churn).
