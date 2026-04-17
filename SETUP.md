# SETUP — Guía Completa de Activación
## VidFlow AI · Sistema de 10 Agentes + Copilot CLI

---

## PASO 0 — Instalar Copilot CLI

```bash
# Instalar GitHub CLI
# Mac:
brew install gh

# Windows:
winget install GitHub.cli

# Linux:
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list
sudo apt update && sudo apt install gh

# Autenticar con GitHub
gh auth login
# → Selecciona: GitHub.com → HTTPS → Yes (authenticate) → Login with browser

# Verificar que Copilot CLI está disponible
gh copilot --version
# Si no lo reconoce, instala la extensión:
gh extension install github/gh-copilot
```

---

## PASO 1 — Clonar y preparar el proyecto

```bash
# Clonar (o usar tu repositorio existente)
git clone https://github.com/TU-USUARIO/vidflow-ai
cd vidflow-ai

# Instalar dependencias Python
pip install -r requirements.txt
pip install openai-whisper

# Instalar ffmpeg
# Mac:       brew install ffmpeg
# Ubuntu:    sudo apt install ffmpeg
# Windows:   winget install Gyan.FFmpeg
```

---

## PASO 2 — Configurar las APIs (todas gratis)

```bash
# Copiar plantilla de .env
cp .env.example .env

# Abrir y rellenar:
nano .env   # o code .env en VS Code
```

Rellena estas variables (el orden importa — empieza por las más fáciles):

```bash
# 1. GEMINI (2 minutos) — ya la tienes
GEMINI_API_KEY=AIzaSy...

# 2. PEXELS (2 minutos) — pexels.com/api → Register → Copy API Key
PEXELS_API_KEY=...

# 3. PIXABAY (2 minutos) — pixabay.com/api/docs → Get API Key
PIXABAY_API_KEY=...

# 4. ELEVENLABS (3 minutos) — elevenlabs.io → Profile → API Keys
ELEVENLABS_API_KEY=...

# 5. MONGODB ATLAS (10 minutos)
#    → mongodb.com/atlas → Create free cluster → Connect → Copy connection string
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/vidflow

# 6. YOUTUBE (15 minutos — el más complejo)
#    → console.cloud.google.com
#    → New Project: "VidFlow AI"
#    → Enable: YouTube Data API v3
#    → Credentials → OAuth 2.0 Client → Desktop App
#    → Download JSON → copy client_id y client_secret
YOUTUBE_CLIENT_ID=...apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=GOCSPX-...

# 7. EMAIL PARA ALERTAS (5 minutos)
#    → Google Account → Security → 2-Step Verification → App Passwords
#    → App: Mail, Device: Other → Generate → copy the 16-char password
EMAIL_FROM=tu@gmail.com
EMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx
```

---

## PASO 3 — Instalar las Skills

```bash
# Crear carpeta de skills
mkdir -p .copilot/skills

# Opción A: Clonar desde GitHub
cd .copilot/skills
git clone https://github.com/coreyhaines31/marketingskills
git clone https://github.com/anthropics/skills anthropic-skills
# Copia solo las skills que necesitas de anthropic-skills/:
cp -r anthropic-skills/skills/frontend-design ./
cp -r anthropic-skills/skills/webapp-testing ./

# Opción B: Instalar la viral-content skill que creamos
# Mueve el archivo viral-content-skill.skill a esta carpeta
# y descomprímelo:
unzip viral-content-skill.skill -d viral-content-generator

cd ../..  # Volver a la raíz del proyecto
```

---

## PASO 4 — Copiar los Agentes

```bash
# Crear carpeta de agentes
mkdir -p .copilot/agents

# Copiar los 10 agentes del zip descargado:
unzip sistema-10-agentes.zip -d .copilot/agents/
# O copiarlos manualmente si los tienes en otra carpeta
```

---

## PASO 5 — Verificar que todo funciona

```bash
python scripts/check_apis.py
```

Verás algo como:
```
📡 APIs Externas:
  Verificando Gemini 2.5 Pro... ✅ Conectado
  Verificando Pexels Video API... ✅ Conectado
  Verificando Pixabay Video API... ✅ Conectado
  Verificando ElevenLabs TTS... ✅ 234 chars usados
  Verificando MongoDB Atlas... ✅ Conectado
  Verificando YouTube OAuth... ✅ Keys presentes

🛠️  Herramientas Locales:
  Verificando ffmpeg... ✅ ffmpeg 6.1.1
  Verificando Whisper... ✅ whisper disponible

✅ TODO LISTO
```

Si hay ❌, sigue las instrucciones que aparecen en pantalla.

---

## PASO 6 — Primer ciclo de prueba

```bash
# Probar UN solo agente primero (el más simple):
bash scripts/run_agent.sh 09
# Debería crear: research/latest_trends.json

# Si funcionó, probar el agente de contenido:
bash scripts/run_agent.sh 02
# Debería crear: content_calendars/*/scripts/YYYY-MM-DD-youtube.md

# Probar el ciclo completo UNA vez:
bash scripts/run_agents.sh --once
# Tarda entre 20-60 minutos la primera vez
```

---

## PASO 7 — Activar el modo continuo (mejora 24h)

```bash
# Arrancar en segundo plano (continúa aunque cierres la terminal)
nohup bash scripts/run_agents.sh --loop > logs/master.log 2>&1 &
echo $! > logs/master.pid
echo "Sistema arrancado con PID $(cat logs/master.pid)"
```

```bash
# Ver qué está pasando en tiempo real (abre otra terminal):
bash scripts/watch_agents.sh
```

```bash
# Para ver los logs directamente:
tail -f logs/master.log

# Para parar el sistema:
kill $(cat logs/master.pid)
```

---

## PASO 8 — Activar GitHub Actions (automatización 24h en la nube)

```bash
# 1. Subir el proyecto a GitHub
git add .
git commit -m "feat: sistema de 10 agentes + pipeline completo"
git push origin main

# 2. Añadir los secrets en GitHub
# Ve a: github.com/TU-USUARIO/vidflow-ai → Settings → Secrets → Actions
# Añade uno a uno con el botón "New repository secret":
```

| Secret Name | Valor |
|---|---|
| GEMINI_API_KEY | Tu key de aistudio.google.com |
| PEXELS_API_KEY | Tu key de pexels.com |
| PIXABAY_API_KEY | Tu key de pixabay.com |
| ELEVENLABS_API_KEY | Tu key de elevenlabs.io |
| MONGODB_URL | Tu connection string de Atlas |
| YOUTUBE_CLIENT_ID | Tu client ID de Google Cloud |
| YOUTUBE_CLIENT_SECRET | Tu client secret de Google Cloud |
| EMAIL_FROM | Tu Gmail |
| EMAIL_APP_PASSWORD | Tu App Password de Google |

```bash
# 3. Activar el workflow manualmente la primera vez para verificar:
gh workflow run daily_pipeline.yml

# 4. Ver el resultado:
gh run list --workflow=daily_pipeline.yml
```

A partir de aquí GitHub Actions corre el pipeline cada día a las 6 AM UTC automáticamente, gratis.

---

## COMANDOS DE USO DIARIO

```bash
# Ver estado del sistema:
bash scripts/watch_agents.sh

# Correr un agente específico:
bash scripts/run_agent.sh 02                    # Content Forge
bash scripts/run_agent.sh trends                # Trend Hunter
bash scripts/run_agent.sh fixer                 # El Fixer

# Correr un agente con contexto:
bash scripts/run_agent.sh 02 "canal: Impacto Mundial, tema: Area 51"

# Arrancar/parar el sistema continuo:
nohup bash scripts/run_agents.sh --loop > logs/master.log 2>&1 &
kill $(cat logs/master.pid)

# Ver el briefing de hoy:
cat briefings/$(date +%Y-%m-%d)-briefing.md

# Ver la cola de vídeos:
python -c "import json; q=json.load(open('pipeline_queue.json')); [print(v['channel'],v['status']) for v in q[-10:]]"

# Preguntarle algo a Copilot con todo el contexto del proyecto:
cat .github/copilot-instructions.md | gh copilot suggest -t shell "mejora el generador de guiones para Mentes Rotas"
```

---

## CÓMO AÑADIR UN NUEVO AGENTE

```bash
# 1. Crear la carpeta
mkdir -p .copilot/agents/agent-11-nuevo/

# 2. Crear el AGENT.md siguiendo esta plantilla:
cat > .copilot/agents/agent-11-nuevo/AGENT.md << 'EOF'
---
name: agent-11-nuevo
description: >
  [Descripción de qué hace este agente]
skills:
  - [skill-name]
memory: .copilot/agents/agent-11-nuevo/memory.json
output: [carpeta-de-outputs]/
---

# Agent 11 — Nombre

## Mission
[Misión del agente en 2-3 frases]

## Protocol
[Pasos que ejecuta]

## Output
[Qué archivos crea]
EOF

# 3. Añadirlo al run_agents.sh en la posición correcta
# 4. Añadirlo al AGENT_MAP en run_agent.sh
# 5. Documentarlo en .github/copilot-instructions.md
```

---

## SOLUCIÓN DE PROBLEMAS

| Problema | Solución |
|---|---|
| `gh copilot: command not found` | `gh extension install github/gh-copilot` |
| Agente no lee los skills | Verifica que la ruta en skills table de copilot-instructions.md es correcta |
| Pantalla negra en vídeos | Corre `bash scripts/run_agent.sh fixer` |
| Pipeline falla silenciosamente | `tail -100 logs/master-$(date +%Y-%m-%d).log` |
| YouTube OAuth expirado | `python pipeline/setup_oauth.py` |
| MongoDB timeout | Verifica IP whitelist en Atlas → Network Access → Add Current IP |
| ElevenLabs quota agotada | El sistema usa Google TTS automáticamente como fallback |
