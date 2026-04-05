name: storytelling-research
description: Realiza una investigación exhaustiva sobre un tema específico para generar un guion de video documental de formato largo. Prioriza fuentes primarias, anécdotas poco conocidas y precisión cronológica.

# Investigación y Guionización Documental

Esta habilidad guía al agente a través de un proceso de investigación web y redacción estructurada.

## Procedimiento de Investigación

1.  **Búsqueda Amplia**: Utiliza el navegador para identificar los hitos principales del tema.
2.  **Minería de Detalles**: Busca específicamente "datos curiosos", "controversias", "diarios personales" o "reportes policiales" relacionados con el tema. La audiencia valora la profundidad.
3.  **Verificación Cruzada**: Todo dato numérico o fecha debe ser verificado en al menos dos fuentes distintas.

## Estructura de Redacción (Formato 15 Minutos)

El guion resultante debe tener aproximadamente 2,500 palabras y seguir estrictamente estas secciones:

| Sección | Tiempo | Objetivo | Instrucción de Tono |
| :--- | :--- | :--- | :--- |
| **Hook** | 00:00-01:00 | Captura inmediata | Urgente, visual, misterioso. Evita saludos. |
| **Contexto** | 01:00-03:00 | Establecer el escenario | Informativo pero con tensión subyacente. |
| **Desarrollo** | 03:00-10:00 | La trama se complica | Ritmo creciente. Usar frases cortas. |
| **Clímax** | 10:00-13:00 | Revelación principal | Dramático, pausado, impactante. |
| **Outro** | 13:00-15:00 | Conclusión y CTA | Reflexivo. |

## Restricciones

-   No utilizar frases cliché como "En el video de hoy..." o "Vamos a sumergirnos".
-   Incluir indicaciones visuales entre corchetes para el agente de edición (ej. `[Corte a imagen de archivo en blanco y negro]`).
-   Priorizar la narrativa sobre la mera exposición de hechos.

## Dependencias

-   Acceso a herramientas de navegación web (`search_web`, `read_url_content`).
-   Acceso a `knowledge-base/` si existe para contexto adicional.
