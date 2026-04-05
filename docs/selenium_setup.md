# Guía: Configuración de Auto-Upload (Método Selenium - 100% GRATIS)

## ✅ Ventajas del Método Selenium

- **100% GRATIS** - Sin APIs, sin cuotas, sin límites
- **Sin configuración de APIs** - No necesitas Google Cloud Console
- **Sin pagos** - Nunca pagarás nada
- **Funciona para siempre** - Mientras tengas cuenta de YouTube/TikTok

## 📦 Instalación

### 1. Instalar Selenium
```bash
pip install selenium
```

### 2. Instalar ChromeDriver
**Opción A: Automático (Recomendado)**
```bash
pip install webdriver-manager
```

**Opción B: Manual**
1. Descargar ChromeDriver: https://chromedriver.chromium.org/downloads
2. Colocar en PATH del sistema

### 3. Verificar instalación
```bash
python -c "from selenium import webdriver; print('✅ Selenium OK')"
```

## 🎬 Uso: YouTube

### Primera vez (Guardar cookies):
```bash
python app/scripts/upload_youtube_selenium.py \
  --video "test.mp4" \
  --title "Test Video" \
  --privacy unlisted
```
- Se abrirá Chrome
- **Inicia sesión en YouTube** manualmente
- Presiona Enter en la terminal
- ✅ Cookies guardadas en `youtube_cookies.txt`

### Siguientes veces (automático):
```bash
python app/scripts/upload_youtube_selenium.py \
  --video "mi_clip.mp4" \
  --title "Mi Clip Viral" \
  --description "Descripción del video" \
  --privacy public
```
- ✅ Login automático con cookies
- ✅ Subida completamente automatizada

## 📱 Uso: TikTok

### Primera vez (Guardar cookies):
```bash
python app/scripts/upload_tiktok_selenium.py \
  --video "test.mp4" \
  --caption "Mi primer TikTok automático"
```
- Se abrirá Chrome
- **Inicia sesión en TikTok** manualmente
- Presiona Enter en la terminal
- ✅ Cookies guardadas en `tiktok_cookies.txt`

### Siguientes veces (automático):
```bash
python app/scripts/upload_tiktok_selenium.py \
  --video "mi_clip.mp4" \
  --caption "Caption con #hashtags"
```

## 🔒 Seguridad de Cookies

Las cookies se guardan localmente en:
- `youtube_cookies.txt`
- `tiktok_cookies.txt`

**IMPORTANTE**: 
- ⚠️ No compartas estos archivos
- ✅ Están en `.gitignore`
- 🔄 Se renuevan automáticamente

## 🛠️ Solución de Problemas

### Error: "Not logged in"
**Solución**: Borrar cookies y volver a hacer login
```bash
rm youtube_cookies.txt
# Volver a ejecutar script
```

### Error: ChromeDriver no encontrado
**Solución**:
```bash
pip install webdriver-manager
```

### Error: Botones no encontrados
**Causa**: YouTube/TikTok cambiaron su interfaz
**Solución**: Los scripts tienen múltiples selectores de fallback, pero si falla:
1. Abrir issue en GitHub
2. O actualizar selectores manualmente

## 🚀 Integración con la App

El endpoint `/api/clips/publish` ya está configurado para usar estos scripts:

```typescript
// Llamada desde ClipViewer
fetch('/api/clips/publish', {
  method: 'POST',
  body: JSON.stringify({
    clipId: '123',
    platform: 'youtube',  // o 'tiktok'
    title: 'Mi Clip',
    description: 'Descripción',
    privacy: 'unlisted'
  })
})
```

## 📊 Comparación: API vs Selenium

| Característica | API Oficial | Selenium |
|----------------|-------------|----------|
| **Costo** | Gratis hasta cuota | 100% Gratis |
| **Setup** | 10 min (OAuth) | 5 min (login manual) |
| **Velocidad** | Rápido | Más lento |
| **Confiabilidad** | Alta | Media |
| **Límites** | Cuota diaria | Sin límites |
| **Mantenimiento** | Cero | Puede necesitar updates |

## ✅ Recomendación

**Usa Selenium** si:
- Quieres evitar configuración de APIs
- Subes pocos videos al día
- Prefieres simplicidad

**Ambos métodos están listos** - tú eliges cuál usar.
