# 🚀 Quick Start - Project Sovereign

## Inicio Rápido (5 minutos)

### 1. Verificar Dependencias

```bash
cd c:\Users\jpima\Downloads\edumind---ai-learning-guide

# Activar entorno virtual
.\venv_sovereign\Scripts\activate

# Verificar dependencias Python
pip install moviepy pillow numpy mediapipe psycopg2-binary pyloudnorm
```

### 2. Iniciar Aplicación Web

```bash
cd app
npm run dev
```

La aplicación estará disponible en: **http://localhost:3001**

### 3. Iniciar Scheduler (Publicaciones Automáticas)

En otra terminal:

```bash
cd c:\Users\jpima\Downloads\edumind---ai-learning-guide
.\venv_sovereign\Scripts\activate
python scripts\schedule_uploads.py
```

El scheduler verificará publicaciones programadas cada 60 segundos.

---

## ✅ Verificación Rápida

### Test 1: Subtítulos
```bash
# Desde la app web:
1. Abre un clip en ClipViewer
2. Click en "📝 Añadir Subtítulos"
3. Confirma (estilo TikTok)
4. Espera 2-5 minutos
5. Verifica en /storage/subtitled/{clipId}.mp4
```

### Test 2: Audio Pro
```bash
# Desde ClipViewer:
1. Click en "🎵 Audio Pro (-14 LUFS)"
2. Confirma
3. El clip será normalizado automáticamente
```

### Test 3: Smart Crop
```bash
# Desde ClipViewer:
1. Click en "🎥 Auto-Reencuadre AI"
2. Confirma
3. El video será convertido a formato vertical centrado en el rostro
```

### Test 4: Publicación Programada
```bash
# Desde la app web:
1. Ve a /calendar
2. Selecciona un clip
3. Arrastra a una fecha
4. Configura título, plataforma (YouTube/TikTok)
5. Guarda
6. El scheduler lo publicará automáticamente a la hora programada
```

---

## 🔧 Funcionalidades Principales

| Función | Ubicación | Estado |
|---------|-----------|--------|
| Generación de Clips con IA | `/` → Pegar URL | ✅ Funcional |
| Subtítulos Automáticos | ClipViewer → 📝 | ✅ Funcional |
| Audio Profesional -14 LUFS | ClipViewer → 🎵 | ✅ Funcional |
| Auto-Reencuadre Inteligente | ClipViewer → 🎥 | ✅ Funcional |
| Limpieza de Muletillas | ClipViewer → ✂️ | ✅ Funcional |
| Publicación Automática | Calendar + Scheduler | ✅ Funcional |
| B-Roll con IA | ClipViewer → 🎬 | ⚠️ En desarrollo |

---

## 📁 Estructura de Almacenamiento

```
app/storage/
├── source/          # Videos originales descargados
├── clips/           # Clips generados (sin procesar)
├── subtitled/       # Clips con subtítulos
├── enhanced/        # Clips con audio mejorado (temporal)
└── previews/        # Previews de baja resolución
```

---

## 🐛 Troubleshooting

### Error: "FFmpeg not found"
```bash
# Asegúrate de que FFmpeg está en PATH
ffmpeg -version
```

### Error: "Database connection failed"
```bash
# Verifica PostgreSQL
psql -U postgres -d edumind_viral -c "SELECT 1"
```

### Error: "Module not found: moviepy"
```bash
.\venv_sovereign\Scripts\activate
pip install moviepy
```

### Scheduler no detecta publicaciones
```bash
# Verifica que hay publicaciones pendientes
psql -U postgres -d edumind_viral -c "
  SELECT id, title, scheduled_at, status 
  FROM scheduled_publications 
  WHERE status = 'pending'
"
```

---

## 🎯 Flujo de Trabajo Recomendado

### Para Crear Contenido Viral:

1. **Pega URL de YouTube** → Genera 20-30 clips automáticamente
2. **Revisa clips** en Dashboard → Ordenados por virality_score
3. **Selecciona top clips** → Abre ClipViewer
4. **Mejora con Enterprise:**
   - Añade subtítulos (TikTok style)
   - Normaliza audio (-14 LUFS)
   - Aplica smart crop (vertical)
   - Limpia muletillas
5. **Descarga o Programa:**
   - Descarga HD directamente
   - O programa publicación automática
6. **Deja que el scheduler trabaje** → Publicación automática a YouTube/TikTok

---

## 📊 Métricas de Rendimiento

**Tiempos estimados:**
- Análisis inicial (Gemini): 2-4 minutos
- Generación de subtítulos: 2-5 minutos por clip
- Normalización de audio: 30-60 segundos por clip
- Smart crop: 3-8 minutos por clip (depende de duración)
- Upload YouTube/TikTok: 2-5 minutos por clip

---

## 🔐 Configuración de Seguridad

### Variables de Entorno Requeridas (.env)

```env
# Base de Datos
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=edumind_viral
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# Gemini AI
GEMINI_API_KEY=your_gemini_key

# Encriptación (opcional)
ENCRYPTION_KEY=generate_with_scripts/encryption.py
```

---

## 🆘 Soporte

Si encuentras algún problema:

1. Revisa los logs:
   - Next.js: Terminal donde corriste `npm run dev`
   - Scheduler: Terminal de `schedule_uploads.py`
   - Scripts Python: Output en consola

2. Verifica archivos generados en `/storage`

3. Consulta `SYSTEM_COMPLETE_DOCUMENTATION.md` para detalles técnicos

---

## ✨ Próximas Funcionalidades (Opcional)

- 🎬 **B-Roll con IA**: Agregar videos de stock automáticamente
- 🔔 **Notificaciones en tiempo real**: SSE para updates de procesamiento
- 📊 **Analytics Dashboard**: Métricas de rendimiento de clips
- 🎨 **Editor visual de subtítulos**: Preview y customización en tiempo real

---

**¡Listo para crear contenido viral! 🚀**
