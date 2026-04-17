# GUÍA COMPLETA — OpenClaw + Sistema VidFlow AI
# De cero a 25 agentes funcionando 24h gratis en tu ordenador
# Con seguridad, chat individual con cada agente e informes de ingresos

---

## QUÉ ES OPENCLAW (y por qué es perfecto para tu sistema)

OpenClaw es un asistente IA de código abierto que se aloja en tu propio ordenador. En lugar de abrir una aplicación nueva, hablas con él a través de las apps de mensajería que ya usas: Telegram, WhatsApp, Discord y más.

Lo que lo hace perfecto para VidFlow AI:
- Los agentes trabajan con un conjunto programado de cron jobs y un heartbeat que se comprueba cada 30 minutos
- Puede ejecutar comandos de terminal, leer y escribir archivos en tu ordenador, automatizar flujos de trabajo, y proactivamente te contacta cuando algo necesita atención
- El sistema de skills de OpenClaw es muy potente — puedes construir skills personalizadas que conectan tu agente con prácticamente cualquier sistema
- Todo corre en tu ordenador — coste $0 salvo los tokens de la API

---

## PASO 1 — INSTALAR OPENCLAW (10 minutos)

### Prerequisitos
```bash
# Verificar que tienes Node.js 24 (o 22 LTS mínimo)
node --version
# Si no lo tienes: https://nodejs.org/en/download

# Verificar npm
npm --version
```

### Instalación
```bash
# Método oficial (1 comando)
npx openclaw@latest onboard --install-daemon
```

El wizard de onboarding configura todo en una sesión: tu proveedor de modelo y API key (Anthropic, OpenAI, Google), tu workspace donde el agente guarda memoria y skills, el gateway (el servidor WebSocket que enruta todo), los canales opcionales como Telegram o WhatsApp, y el daemon en segundo plano para que el gateway siga corriendo sin que tengas que hacer nada.

Durante el onboarding, cuando te pregunte:
- **Model provider:** Anthropic
- **API Key:** tu ANTHROPIC_API_KEY (de console.anthropic.com)
- **Model:** `claude-opus-4-6` (el mejor para agentes autónomos)
- **Workspace:** `/ruta/a/vidflow-project/.openclaw/workspace`
- **Install daemon:** SÍ (imprescindible para 24h)

### Verificar que funciona
```bash
# Ver estado del gateway
openclaw gateway status
# Debe mostrar: Runtime: running | RPC probe: ok

# Abrir el panel de control en el navegador
# Ve a: http://localhost:18789
```

---

## PASO 2 — CONECTAR TELEGRAM (3 minutos)

Telegram es el canal recomendado para empezar. La API oficial de bots es estable, bien documentada y tarda unos 3 minutos en configurar.

```
1. Abre Telegram → busca @BotFather
2. Envía: /newbot
3. Nombre del bot: VidFlow AI
4. Username: vidflow_ai_bot (debe terminar en "bot")
5. BotFather te da un token: 1234567890:ABCDEF...
6. Copia ese token
```

```bash
# Añadir el token de Telegram a OpenClaw
openclaw config set channels.telegram.token "TU_TOKEN_AQUI"
openclaw config set channels.telegram.allowFrom ["TU_TELEGRAM_USER_ID"]
openclaw gateway restart
```

Para saber tu Telegram User ID: busca @userinfobot en Telegram y envíale /start.

Ahora escríbele al bot en Telegram. Debe responder en segundos.

---

## PASO 3 — CONFIGURAR LA SEGURIDAD (crítico)

Empieza conservador: configura siempre channels.telegram.allowFrom (nunca dejes el sistema abierto a cualquiera). Usa un número de WhatsApp dedicado para el asistente. Los heartbeats por defecto son cada 30 minutos — desactívalos hasta que confíes en la configuración poniendo agents.defaults.heartbeat.every: "0m".

Crea `.openclaw/config.yaml`:
```yaml
logging:
  level: "info"

agent:
  model: "anthropic/claude-opus-4-6"
  workspace: "./vidflow-project/.openclaw/workspace"
  thinkingDefault: "medium"
  timeoutSeconds: 1800
  heartbeat:
    every: "30m"    # Los agentes se "despiertan" cada 30 min

channels:
  telegram:
    token: "${TELEGRAM_BOT_TOKEN}"
    allowFrom:
      - "${TU_TELEGRAM_USER_ID}"  # Solo tú puedes enviar comandos

security:
  # Carpetas donde los agentes PUEDEN escribir
  allowedPaths:
    - "./vidflow-project/"
    - "./.openclaw/workspace/"
  
  # Carpetas PROTEGIDAS (los agentes no pueden tocar)
  blockedPaths:
    - "~/"                      # Home directory completo
    - "/etc/"                   # Configuración del sistema
    - "/usr/"                   # Programas del sistema
    - "./vidflow-project/.env"  # Credenciales (solo lectura)
    - "./vidflow-project/.git/" # Historial de git

  # Comandos que los agentes PUEDEN ejecutar
  allowedCommands:
    - "python"
    - "pip"
    - "ffmpeg"
    - "ffprobe"
    - "git commit"
    - "git push"

  # Comandos BLOQUEADOS
  blockedCommands:
    - "rm -rf"
    - "sudo"
    - "chmod 777"
    - "curl | bash"
    - "wget | bash"

session:
  scope: "per-agent"
  reset:
    mode: "daily"
    atHour: 4
```

### Regla de seguridad más importante

No instales OpenClaw en un ordenador de trabajo o personal que estés usando activamente. Trátalo como un ejecutor de scripts que toma instrucciones literalmente.

**Para VidFlow, usa una carpeta dedicada y con los paths restringidos al proyecto.**

---

## PASO 4 — CREAR LOS 25 AGENTES EN OPENCLAW

OpenClaw gestiona múltiples agentes con identidades propias. Cada agente tiene:
- Su propio archivo de configuración
- Su propia memoria persistente
- Sus propias skills
- Su propio canal de Telegram (o el mismo, filtrando por nombre)

### Estructura de agentes en OpenClaw

```
.openclaw/
├── workspace/
│   ├── agents/
│   │   ├── patriarch/
│   │   │   ├── agent.yaml       ← configuración del agente
│   │   │   ├── memory.md        ← memoria persistente (OpenClaw escribe aquí)
│   │   │   ├── skills/          ← skills específicas de este agente
│   │   │   └── sessions/        ← historial de sesiones
│   │   ├── researcher/
│   │   ├── content-forge/
│   │   └── [... 22 agentes más]
│   ├── shared-memory/           ← memoria compartida entre todos
│   │   ├── income_tracker.json
│   │   ├── pipeline_queue.json
│   │   └── team_updates.md
│   └── skills/                  ← skills disponibles para todos
```

### Archivo de configuración de agente (ejemplo: Agent-02 Content Forge)

`.openclaw/workspace/agents/content-forge/agent.yaml`:
```yaml
name: "Content Forge"
id: "agent-02-content-forge"
emoji: "✍️"
description: "Generates complete YouTube and TikTok scripts for all 6 channels"
model: "anthropic/claude-opus-4-6"

# Personalidad y misión (se incluye en cada prompt)
identity: |
  Eres Content Forge, el creador de contenido del equipo VidFlow AI.
  Conviertes insights y tendencias en guiones virales y monetizables.
  Tu único objetivo es generar vídeos que la gente quiera ver Y que generen ingresos.
  Piensas de forma creativa e independiente. Cuando ves una oportunidad, la tomas.

# Archivos de contexto que lee al inicio de cada sesión
contextFiles:
  - "../shared-memory/pipeline_queue.json"
  - "../shared-memory/team_updates.md"
  - "../../research/latest_trends.json"
  - "memory.md"

# Skills disponibles para este agente
skills:
  - "../../skills/viral-content-generator"
  - "../../skills/marketingskills"
  - "../../skills/web-research"
  - "../shared-skills/file-manager"

# Herramientas que puede usar
tools:
  - browser: true          # Puede buscar en internet
  - fileSystem: true       # Puede leer/escribir archivos del proyecto
  - exec: false            # NO puede ejecutar comandos (solo Content)
  - webSearch: true        # Búsqueda web activa

# Heartbeat: qué hace cuando nadie le habla
heartbeat:
  every: "6h"              # Se activa cada 6 horas
  task: |
    Revisa si hay nuevos trending topics en research/latest_trends.json.
    Si hay trending topics sin guión asignado, genera el guión para el canal más relevante.
    Actualiza pipeline_queue.json con el nuevo vídeo.
    Escribe en shared-memory/team_updates.md qué has creado.

# Comando de diario: qué escribe cada día
dailyDiary:
  at: "23:30"
  writeTo: "../../diary/agent-02-diary.md"
  prompt: |
    Escribe una entrada de diario de hoy en primera persona, en español natural.
    Incluye: qué guiones generaste, qué decidiste y por qué, qué encontraste interesante,
    y qué planeas hacer mañana.
```

---

## PASO 5 — SCRIPT DE CREACIÓN AUTOMÁTICA DE LOS 25 AGENTES

Pega este prompt en Copilot para que cree todos los archivos de configuración:

```
Lee el archivo prompts/PROMPT_01_SISTEMA_AGENTES_MAESTRO.md para entender
la misión de cada agente. Luego crea un archivo agent.yaml en
.openclaw/workspace/agents/[nombre-agente]/ para cada uno de los 25 agentes.

Cada agent.yaml debe tener:
- name, id, emoji, description, model: claude-opus-4-6
- identity: la misión específica del agente en primera persona, en español
- contextFiles: los archivos relevantes para ese agente
- skills: las skills del .copilot/skills/ que ese agente necesita
- tools: browser=true para agentes de investigación, exec=true para técnicos
- heartbeat: qué hace el agente cada X horas cuando nadie le habla
  (adaptar la frecuencia: agentes de producción cada 4h, análisis cada 8h, código cada 12h)
- dailyDiary: a qué hora escribe su diario y qué incluir

Agentes con exec:true (pueden ejecutar código):
03-code-sentinel, 08-fixer, 12-performance, 10-scheduler

Agentes con browser:true (pueden navegar):
01-researcher, 09-trend-hunter, 24-net-forager, 06-money-finder, 11-video-quality

Todos los demás: solo fileSystem y webSearch.

Después de crear todos los archivos, genera el script
.openclaw/start_all_agents.sh que inicie todos los agentes con OpenClaw.
```

---

## PASO 6 — CÓMO HABLAR CON CADA AGENTE INDIVIDUALMENTE

En Telegram, usa este formato para dirigirte a un agente específico:

```
@[nombre_agente]: [tu mensaje]

Ejemplos:
@researcher: ¿Qué tendencias has encontrado hoy para Wealth Files?
@content-forge: Genera un guión sobre los Panama Papers para mañana
@money-finder: ¿Cuánto hemos ganado esta semana en afiliados?
@patriarch: Dame el resumen del equipo de hoy
@fixer: Hay un error en el pipeline, míralo
```

OpenClaw ruteará el mensaje al agente correcto y recibirás la respuesta
del agente específico, con su personalidad y contexto propios.

Para configurar esto, en `.openclaw/config.yaml`:
```yaml
routing:
  agentMentions:
    enabled: true
    format: "@{agentName}: {message}"
    defaultAgent: "patriarch"  # Si no mencionas agente, va al Patriarca
```

---

## PASO 7 — INFORME DIARIO AUTOMÁTICO DE INGRESOS

Configura que a las 20:00 todos los días, el Patriarca te mande un informe.

En `.openclaw/workspace/agents/patriarch/agent.yaml`:
```yaml
scheduledTasks:
  - name: "daily-income-report"
    cron: "0 20 * * *"    # Cada día a las 20:00
    task: |
      Es hora del informe diario. Reúne información de todos los agentes:
      
      1. Lee monetization/income_tracker.json para ingresos estimados
      2. Lee analytics/weekly-report.json si existe
      3. Lee diary/ de cada agente para saber qué hicieron hoy
      4. Lee pipeline_queue.json para estado de vídeos
      5. Lee NEEDS_FROM_HUMAN.md para pendientes
      
      Escribe y ENVÍA por Telegram un informe en español con:
      
      📊 INFORME DIARIO — [FECHA]
      
      💰 INGRESOS HOY
      [fuente por fuente con estimados]
      Total estimado este mes: $X
      
      ✅ LO QUE HIZO EL EQUIPO HOY
      [resumen de 3-4 líneas de los agentes más activos]
      
      📹 VÍDEOS
      [cuántos generados, subidos, en cola]
      
      ⚠️ NECESITO TU AYUDA
      [si hay algo en NEEDS_FROM_HUMAN.md]
      
      🎯 MAÑANA EL EQUIPO TRABAJARÁ EN
      [preview del trabajo de mañana]
      
      Sé conciso. El informe no debe tardar más de 1 minuto en leer.
    
    sendTo: "telegram:${TU_TELEGRAM_USER_ID}"
```

---

## PASO 8 — MANTENER TODO SEGURO

### Lo que OpenClaw NUNCA debe poder hacer
```yaml
# En .openclaw/config.yaml — security section
security:
  hardBlocks:
    - pattern: "rm -rf /"
    - pattern: "sudo"
    - pattern: "format"
    - pattern: "DROP TABLE"
    - pattern: "DELETE FROM"     # Proteger base de datos
    - pattern: ".env"            # No modificar credenciales
    - pattern: "git push --force"
    - pattern: "stripe"          # No tocar pagos
    - pattern: "paypal"
```

### Backup automático antes de cambios importantes
```yaml
security:
  beforeWrite:
    createBackup: true
    backupPath: ".openclaw/backups/"
    keepBackups: 7  # 7 días de backups
```

### Modo read-only para agentes no técnicos
Los agentes de contenido (02, 04, 18, 19, 23) no necesitan escribir código.
Configúralos con `tools.exec: false` y `tools.fileSystem: "read-write-content-only"`.

---

## PASO 9 — ARRANCAR EL SISTEMA COMPLETO

```bash
# 1. Arrancar el gateway de OpenClaw (si no está como daemon)
openclaw gateway start

# 2. Verificar que todos los agentes están cargados
openclaw agents list

# 3. Hacer un test con el Patriarca
# En Telegram: @patriarch hola, ¿estás listo?

# 4. Lanzar el primer ciclo completo
# En Telegram: @scheduler ejecuta el ciclo completo de hoy

# 5. Ver los logs en tiempo real
openclaw logs --tail --agent all
```

---

## CÓMO FUNCIONA EL SISTEMA 24H

```
Cada 30 minutos: OpenClaw "despierta" y comprueba si algún agente
                 tiene un heartbeat pendiente
                 
Cada 4-8 horas: Los agentes activos ejecutan su tarea heartbeat
                (generar contenido, buscar tendencias, revisar código)
                
Cada día a las 06:00: GitHub Actions ejecuta el ciclo completo del pipeline
                       (generar → ensamblar → verificar calidad → subir)
                       
Cada día a las 20:00: El Patriarca te envía el informe por Telegram

Cuando tú escribes: OpenClaw enruta tu mensaje al agente correcto
                    y te responde en segundos
```

El sistema funciona 24h porque:
1. El daemon de OpenClaw arranca automáticamente con tu ordenador
2. Los heartbeats activan los agentes sin intervención humana
3. GitHub Actions ejecuta el pipeline aunque el ordenador esté durmiendo
4. Los agentes se comunican entre sí a través de archivos compartidos
