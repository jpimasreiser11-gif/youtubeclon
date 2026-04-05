# Guía de Configuración Final

## 🚀 Setup Inicial (5 minutos)

### 1. Instalar Dependencias Python
```bash
pip install selenium cryptography webdriver-manager
```

### 2. Generar Clave de Encriptación
```bash
python app/scripts/encryption.py --generate-key
# Copia la salida y añádela a tu .env:
# ENCRYPTION_KEY=...
```

### 3. Configurar YouTube Upload
```bash
# Primera vez: guardará cookies automáticamente
python app/scripts/upload_youtube_selenium.py \
  --video "test.mp4" \
  --title "Test Upload"

# Se abrirá Chrome, inicia sesión, presiona Enter
# Cookies guardadas en youtube_cookies.txt ✅
```

### 4. Configurar TikTok Upload
```bash
# Primera vez: guardará cookies automáticamente
python app/scripts/upload_tiktok_selenium.py \
  --video "test.mp4" \
  --caption "Test TikTok"

# Se abrirá Chrome, inicia sesión, presiona Enter
# Cookies guardadas en tiktok_cookies.txt ✅
```

## 📖 Uso del Sistema

### Crear Proyecto y Analizar Video
1. Ve a la página principal
2. Pega URL de YouTube
3. Click "Analizar Video con IA"
4. Espera ~2-5 minutos
5. ✅ 20-30 clips generados automáticamente

### Ver y Editar Clips
1. Dashboard → Click en proyecto completado
2. Studio → Selecciona clip de la lista
3. Ver análisis de IA (gancho, resolución, score)
4. Click "Editar clip" para ajustar tiempos
5. Click "Subtítulos" para personalizar

### Publicar en Redes Sociales
**Opción 1: Publicación Inmediata**
1. En ClipViewer → "Publicar en redes sociales"
2. Selecciona plataforma (YouTube/TikTok)
3. ✅ Upload automático en background

**Opción 2: Programar Publicación**
1. Calendar → Selecciona clip de sidebar
2. Click en fecha del calendario
3. Elige YouTube o TikTok
4. ✅ Se publicará automáticamente ese día

### Optimizar Videos
```bash
# Crear versión vertical con blur
python app/scripts/video_processor.py \
  --input "video.mp4" \
  --output "vertical.mp4" \
  --mode vertical \
  --start 10 --end 60

# Optimizar para TikTok
python app/scripts/video_processor.py \
  --input "clip.mp4" \
  --output "tiktok.mp4" \
  --mode optimize \
  --platform tiktok
```

## 🔐 Seguridad

### Encriptar Tokens
```python
from scripts.encryption import encrypt_token, decrypt_token

# Encriptar
encrypted = encrypt_token("mi-token-secreto")

# Desencriptar
original = decrypt_token(encrypted)
```

## 🎯 Flujo Completo Típico

1. **Subir video** → Sistema genera 20-30 clips
2. **Revisar en Studio** → Ver scores de viralidad
3. **Editar top clips** → Ajustar tiempos, añadir subtítulos
4. **Programar publicaciones** → Calendario visual
5. **Auto-publish** → Sistema publica automáticamente

## 💡 Tips

- **Clips destacados**: Los primeros 6 clips tienen score >90 (top viral)
- **Subtítulos**: Usa preset "TikTok" para videos virales
- **Programación**: Programa 1-2 clips al día para engagement constante
- **Vertical crop**: Usa blur background para videos horizontales

## 📊 Monitoreo

- **Dashboard**: Ve estadísticas generales
- **Calendar**: Publicaciones programadas
- **Studio**: Score de viralidad de cada clip
