# 📱 PROJECT SOVEREIGN - ANÁLISIS COMPLETO DE CÓDIGO

> **Propósito de este documento:** Proporcionar una visión completa del código de la aplicación para análisis, mejora y solución de problemas por parte de modelos de IA (ChatGPT, Gemini, etc.)

---

## 📊 ARQUITECTURA GENERAL

### Stack Tecnológico
- **Frontend:** Next.js 14 (App Router), React, TypeScript
- **Backend:** Next.js API Routes, Python scripts
- **Base de Datos:** PostgreSQL
- **IA:** Google Gemini 2.0 Flash
- **Procesamiento de Video:** FFmpeg, MoviePy, Whisper
- **Automatización:** Selenium (YouTube/TikTok uploads)
- **Autenticación:** NextAuth.js

### Flujo Principal
```
Usuario → Next.js Frontend → API Routes → Python Scripts → FFmpeg/MoviePy → Storage → DB
                                    ↓
                              Gemini AI Analysis
                                    ↓
                           Video Clips Generation
```

---

## 🗂️ ESTRUCTURA DE DIRECTORIOS

```
edumind---ai-learning-guide/
├── app/                          # Aplicación Next.js
│   ├── app/                      # App Router de Next.js
│   │   ├── page.tsx             # Página principal (HOME)
│   │   ├── login/               # Autenticación
│   │   ├── studio/              # Vista de clips generados
│   │   ├── calendar/            # Programación de publicaciones
│   │   └── api/                 # API Routes
│   │       ├── process/         # Procesamiento de videos
│   │       ├── clips/           # Gestión de clips
│   │       └── get-metadata/    # Obtener metadata de YouTube
│   ├── components/              # Componentes React
│   ├── lib/                     # Utilidades y DB
│   └── storage/                 # Almacenamiento de videos
├── scripts/                     # Scripts Python
│   ├── ingest.py               # Procesamiento inicial
│   ├── clipper.py              # Generación de clips
│   ├── render_viral.py         # Renderizado con subtítulos
│   ├── smart_crop.py           # Recorte inteligente
│   ├── audio_processor.py      # Normalización de audio
│   ├── schedule_uploads.py     # Scheduler automático
│   └── upload_*.py             # Scripts de upload
└── docs/                        # Documentación
```

---

## 🎯 COMPONENTES PRINCIPALES

### 1. PÁGINA PRINCIPAL (app/app/page.tsx)

**Propósito:** Gestionar el flujo de ingesta de videos de YouTube

**Funcionalidades principales:**
- Input de URL de YouTube
- Fetch de metadata (título, thumbnail, duración)
- Trigger de procesamiento
- Visualización de progreso
- Display de clips generados

**Estado principal:**
```typescript
const [url, setUrl] = useState('');              // URL del video
const [metadata, setMetadata] = useState(null);   // Metadata de YouTube
const [processing, setProcessing] = useState(false);
const [projectId, setProjectId] = useState(null);
const [clips, setClips] = useState([]);
```

**Flujo de trabajo:**
```
1. Usuario pega URL → fetchMetadata()
2. Preview del video → Usuario confirma
3. handleProcess() → POST /api/process
4. Polling cada 5s → GET /api/projects/{id}/status
5. Cuando complete → Muestra clips generados
```

**PROBLEMAS IDENTIFICADOS:**
- ⚠️ Falta validación robusta de URL
- ⚠️ No hay manejo de timeouts en polling
- ⚠️ Falta feedback visual detallado del progreso

---

### 2. API ROUTE: PROCESS (app/app/api/process/route.ts)

**Propósito:** Iniciar el procesamiento de un video de YouTube

**Código actual:**
```typescript
export async function POST(request: Request) {
    const session = await auth();
    if (!session?.user) {
        return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { url, title, thumbnail } = await request.json();
    
    // Crear proyecto en DB
    const project = await createProject(url, title, thumbnail);
    
    // Trigger Python script
    const pythonPath = 'c:\\...\\venv_sovereign\\Scripts\\python.exe';
    const scriptPath = 'c:\\...\\scripts\\ingest.py';
    
    exec(`"${pythonPath}" "${scriptPath}" --url "${url}" --project-id "${project.id}"`, 
        { timeout: 1800000 }, // 30 min
        (error, stdout, stderr) => {
            if (error) {
                console.error('Error:', error);
                updateProjectStatus(project.id, 'failed');
            } else {
                updateProjectStatus(project.id, 'completed');
            }
        }
    );
    
    return NextResponse.json({ projectId: project.id });
}
```

**PROBLEMAS IDENTIFICADOS:**
- ⚠️ Usa callbacks en lugar de async/await
- ⚠️ No hay logging estructurado
- ⚠️ Falta manejo de errores específicos
- ⚠️ Timeout muy alto (30 min)

**MEJORA SUGERIDA:**
```typescript
// Usar promisify para mejor manejo
const execAsync = promisify(exec);

try {
    const { stdout, stderr } = await execAsync(cmd, { timeout: 1800000 });
    // Parse stdout para obtener progreso
    // Actualizar DB con resultados
} catch (error) {
    // Manejo específico de errores
    await updateProjectStatus(project.id, 'failed', error.message);
    throw error;
}
```

---

### 3. SCRIPT: INGEST.PY

**Propósito:** Descargar video, transcribir, analizar con Gemini y generar clips

**Flujo detallado:**
```python
def main(url, project_id):
    # 1. Descargar video con yt-dlp
    video_path = download_youtube_video(url)
    
    # 2. Extraer audio
    audio_path = extract_audio(video_path)
    
    # 3. Transcribir con Whisper
    transcript = transcribe_audio(audio_path)
    
    # 4. Analizar con Gemini
    clips_data = analyze_with_gemini(transcript, video_path)
    
    # 5. Para cada clip sugerido:
    for clip in clips_data:
        # Cortar video
        clip_path = cut_video(video_path, clip['start'], clip['end'])
        
        # Aplicar smart crop (opcional)
        if ENABLE_SMART_CROP:
            clip_path = smart_crop(clip_path)
        
        # Guardar en DB
        save_clip_to_db(project_id, clip)
    
    # 6. Actualizar proyecto
    update_project_status(project_id, 'completed')
```

**PROBLEMAS IDENTIFICADOS:**
- ⚠️ No hay checkpoints para reintentos
- ⚠️ Si falla en medio, se pierde todo el progreso
- ⚠️ Falta logging detallado
- ⚠️ No hay límite de clips generados (puede generar 100+)

**MEJORA SUGERIDA:**
- Implementar sistema de checkpoints
- Guardar transcripción en DB antes de análisis
- Limitar clips a 30 máximo
- Agregar retry logic en llamadas a Gemini

---

### 4. COMPONENTE: ClipViewer (app/components/ClipViewer.tsx)

**Propósito:** Visualizar y gestionar clips individuales

**Funcionalidades implementadas:**
```typescript
// Botones funcionales
- ✅ Publicar en redes sociales
- ✅ Exportar XML
- ✅ Descargar HD
- ✅ Editar clip (timeline)
- ✅ Añadir Subtítulos (IA)
- ✅ Audio Pro (-14 LUFS)
- ✅ Auto-Reencuadre AI
- ✅ Limpiar Muletillas
- ⚠️ Añadir B-roll AI (pendiente)
```

**Handlers implementados:**
```typescript
const handleAddSubtitles = async () => {
    const res = await fetch('/api/clips/add-subtitles', {
        method: 'POST',
        body: JSON.stringify({ clipId: clip.id, style: 'tiktok' })
    });
    // Muestra resultado
};
```

**PROBLEMAS IDENTIFICADOS:**
- ⚠️ Usa `alert()` para feedback (no es profesional)
- ⚠️ No hay indicador de progreso durante procesamiento
- ⚠️ Falta manejo de errores detallado
- ⚠️ No actualiza preview después de aplicar cambios

**MEJORA SUGERIDA:**
```typescript
// Usar toast notifications en lugar de alert
import { toast } from 'react-hot-toast';

const handleAddSubtitles = async () => {
    toast.loading('Generando subtítulos...');
    try {
        const res = await fetch('/api/clips/add-subtitles', {
            method: 'POST',
            body: JSON.stringify({ clipId: clip.id, style: 'tiktok' })
        });
        const data = await res.json();
        if (data.success) {
            toast.success('Subtítulos agregados!');
            refreshClipPreview(); // Actualizar preview
        } else {
            toast.error(data.error);
        }
    } catch (error) {
        toast.error('Error al generar subtítulos');
    }
};
```

---

### 5. API ROUTE: ADD-SUBTITLES (app/app/api/clips/add-subtitles/route.ts)

**Código actual:**
```typescript
export async function POST(request: Request) {
    const { clipId, style = 'tiktok' } = await request.json();
    
    // Verificar clip existe
    const clip = await getClipFromDB(clipId);
    if (!clip) return NextResponse.json({ error: 'Clip not found' }, { status: 404 });
    
    // Ejecutar script Python
    const cmd = `"${pythonPath}" "${renderScript}" --clip-id "${clipId}" --style "${style}"`;
    
    const { stdout, stderr } = await execAsync(cmd, { timeout: 300000 }); // 5 min
    
    // Parsear resultado
    const result = JSON.parse(stdout);
    
    if (result.success) {
        // Actualizar DB
        await updateClipEdits(clipId, { has_subtitles: true, subtitle_style: style });
        return NextResponse.json({ success: true, output: result.output });
    }
}
```

**PROBLEMAS IDENTIFICADOS:**
- ⚠️ No valida que exista transcripción antes de generar subtítulos
- ⚠️ Falta manejo de errores si el script Python falla
- ⚠️ No hay logging del progreso

---

### 6. SCRIPT: render_with_subtitles.py

**Propósito:** Renderizar video con subtítulos quemados

**Código simplificado:**
```python
def render_with_subtitles(video_path, output_path, words, style_name='tiktok'):
    """
    Args:
        video_path: Ruta del video de entrada
        output_path: Ruta del video de salida
        words: Lista de palabras con timestamps [{word, start, end}]
        style_name: Estilo de subtítulos (tiktok, youtube_shorts, instagram_reels)
    """
    # Cargar video
    clip = VideoFileClip(video_path)
    
    # Obtener estilo
    style = STYLES.get(style_name, STYLES['tiktok'])
    
    # Crear TextClips para cada palabra
    subtitle_clips = []
    for word_data in words:
        txt_clip = TextClip(
            word_data['word'],
            fontsize=style['fontsize'],
            color=style['color'],
            font=style['font'],
            stroke_color=style.get('stroke_color', 'black'),
            stroke_width=style.get('stroke_width', 2)
        ).set_position(style['position']).set_start(word_data['start']).set_duration(word_data['end'] - word_data['start'])
        
        subtitle_clips.append(txt_clip)
    
    # Componer video + subtítulos
    final = CompositeVideoClip([clip] + subtitle_clips)
    
    # Renderizar
    final.write_videofile(output_path, codec='libx264', audio_codec='aac')
```

**PROBLEMAS IDENTIFICADOS:**
- ⚠️ MoviePy es muy lento para videos largos
- ⚠️ No hay logs de progreso
- ⚠️ Falta optimización (puede usar threads)
- ⚠️ Si falla a mitad, no hay forma de reintentar desde checkpoint

**MEJORA SUGERIDA:**
```python
# Usar pil_subtitle_renderer.py en su lugar (más rápido)
# Agregar progress callback
def render_with_subtitles(video_path, output_path, words, style_name='tiktok', progress_callback=None):
    # ...
    final.write_videofile(
        output_path, 
        codec='libx264',
        logger=progress_callback  # Callback para progreso
    )
```

---

### 7. SCHEDULER: schedule_uploads.py

**Propósito:** Daemon para publicaciones automáticas programadas

**Código simplificado:**
```python
class UploadScheduler:
    def run(self):
        while True:
            # Obtener publicaciones pendientes
            publications = self.get_pending_uploads()  # WHERE scheduled_at <= NOW()
            
            for pub in publications:
                self.mark_as_processing(pub['id'])
                
                if pub['platform'] == 'youtube':
                    success, result = self.upload_to_youtube(pub)
                elif pub['platform'] == 'tiktok':
                    success, result = self.upload_to_tiktok(pub)
                
                if success:
                    self.mark_as_completed(pub['id'], video_url=result)
                else:
                    self.mark_as_failed(pub['id'], error=result)
            
            time.sleep(60)  # Check cada minuto
```

**PROBLEMAS IDENTIFICADOS:**
- ⚠️ No hay manejo de múltiples instancias (puede duplicar uploads)
- ⚠️ Falta retry logic si falla un upload
- ⚠️ No hay límite de rate (puede saturar APIs)
- ⚠️ Falta monitoreo de salud del scheduler

**MEJORA SUGERIDA:**
```python
# Agregar lock para evitar duplicados
def get_pending_uploads(self):
    cursor.execute("""
        UPDATE scheduled_publications 
        SET status = 'processing', processing_started_at = NOW()
        WHERE id IN (
            SELECT id FROM scheduled_publications
            WHERE status = 'pending' AND scheduled_at <= NOW()
            LIMIT 1
            FOR UPDATE SKIP LOCKED  -- Evita duplicados
        )
        RETURNING *
    """)
```

---

### 8. SCRIPT: audio_processor.py

**Propósito:** Normalizar audio a -14 LUFS profesional

**Código:**
```python
def normalize_audio_pro(input_file, output_file, target_lufs=-14):
    # Primera pasada: analizar
    stats = analyze_loudness(input_file)
    
    # Segunda pasada: normalizar con stats medidos
    loudnorm_filter = f"loudnorm=I={target_lufs}:measured_I={stats['input_i']}:..."
    
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-af', loudnorm_filter,
        '-c:v', 'copy',  # No re-encodear video
        '-c:a', 'aac',
        output_file
    ]
    
    subprocess.run(cmd, check=True)
```

**MEJORAS POSIBLES:**
- ✅ Ya usa two-pass loudnorm (óptimo)
- ⚠️ Podría agregar detección de silence para cortar partes sin audio
- ⚠️ Falta opción de fade in/out

---

### 9. BASE DE DATOS: Schema Principal

```sql
-- PROYECTOS
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    url TEXT NOT NULL,
    title TEXT,
    thumbnail TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    created_at TIMESTAMP DEFAULT NOW()
);

-- CLIPS GENERADOS
CREATE TABLE clips (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    rank INT,
    start_time FLOAT,
    end_time FLOAT,
    virality_score INT,
    title TEXT,
    category TEXT,
    hook_description TEXT,
    payoff_description TEXT,
    reason TEXT,
    transcript TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- EDICIONES DE CLIPS
CREATE TABLE clip_edits (
    clip_id UUID PRIMARY KEY REFERENCES clips(id),
    has_subtitles BOOLEAN DEFAULT false,
    subtitle_style JSONB,
    zoom_data JSONB,
    audio_normalized BOOLEAN DEFAULT false,
    disfluencies_removed BOOLEAN DEFAULT false,
    has_broll BOOLEAN DEFAULT false,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- TRANSCRIPCIONES
CREATE TABLE transcriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clip_id UUID REFERENCES clips(id),
    words JSONB NOT NULL,  -- [{word, start, end, confidence}]
    created_at TIMESTAMP DEFAULT NOW()
);

-- PUBLICACIONES PROGRAMADAS
CREATE TABLE scheduled_publications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clip_id UUID REFERENCES clips(id),
    platform VARCHAR(50),  -- youtube, tiktok
    scheduled_at TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- pending, processing, published, failed
    title TEXT,
    description TEXT,
    tags TEXT,
    privacy VARCHAR(20),
    video_url TEXT,
    error_message TEXT,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- HISTORIAL DE UPLOADS
CREATE TABLE upload_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clip_id UUID REFERENCES clips(id),
    platform VARCHAR(50),
    status VARCHAR(20),
    video_url TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**PROBLEMAS IDENTIFICADOS:**
- ⚠️ Falta índices en columnas frecuentemente consultadas
- ⚠️ No hay constraint para evitar publicaciones duplicadas
- ⚠️ Falta tabla de analytics/metrics

---

## 🚨 PROBLEMAS CRÍTICOS IDENTIFICADOS

### 1. **Manejo de Errores Inconsistente**
- Algunos endpoints usan callbacks
- Otros usan async/await
- Falta logging estructurado

### 2. **Falta de Validación**
- No se validan inputs de usuario
- URLs pueden ser maliciosas
- Falta sanitización de datos

### 3. **Performance**
- MoviePy es extremadamente lento
- No hay caching de resultados
- Falta optimización de queries DB

### 4. **Seguridad**
- Paths hardcodeados en código
- Falta rate limiting
- No hay encryption de tokens sensibles

### 5. **UX/UI**
- Feedback con `alert()` es pobre
- Falta indicadores de progreso
- No hay sistema de notificaciones

---

## 💡 PLAN DE MEJORAS PRIORITARIAS

### ALTA PRIORIDAD

1. **Migrar todos los exec() a execAsync con promisify**
   - Mejor manejo de errores
   - Más fácil de debuggear
   - Timeouts más controlables

2. **Implementar sistema de logging estructurado**
   ```typescript
   import winston from 'winston';
   
   const logger = winston.createLogger({
       level: 'info',
       format: winston.format.json(),
       transports: [
           new winston.transports.File({ filename: 'error.log', level: 'error' }),
           new winston.transports.File({ filename: 'combined.log' })
       ]
   });
   ```

3. **Agregar validación de inputs**
   ```typescript
   import { z } from 'zod';
   
   const ProcessSchema = z.object({
       url: z.string().url().includes('youtube.com'),
       title: z.string().max(200),
       thumbnail: z.string().url().optional()
   });
   ```

4. **Implementar sistema de notificaciones con toast**
   ```typescript
   import { Toaster } from 'react-hot-toast';
   // Reemplazar todos los alert() con toast.*
   ```

5. **Optimizar renderizado de subtítulos**
   - Usar `pil_subtitle_renderer.py` en lugar de MoviePy
   - Implementar parallel processing
   - Agregar progress callbacks

### MEDIA PRIORIDAD

6. **Agregar índices a DB**
   ```sql
   CREATE INDEX idx_clips_project_id ON clips(project_id);
   CREATE INDEX idx_scheduled_publications_status ON scheduled_publications(status, scheduled_at);
   ```

7. **Implementar retry logic**
   ```typescript
   async function retryWithBackoff(fn, maxRetries = 3) {
       for (let i = 0; i < maxRetries; i++) {
           try {
               return await fn();
           } catch (error) {
               if (i === maxRetries - 1) throw error;
               await sleep(Math.pow(2, i) * 1000);
           }
       }
   }
   ```

8. **Agregar sistema de checkpoints en ingest.py**
   ```python
   def save_checkpoint(project_id, stage, data):
       # Guardar en DB o archivo
       pass
   
   def resume_from_checkpoint(project_id):
       # Recuperar último checkpoint
       pass
   ```

### BAJA PRIORIDAD

9. **Implementar analytics dashboard**
10. **Crear tests unitarios y de integración**
11. **Optimizar caching y CDN**

---

## 📋 CHECKLIST DE VERIFICACIÓN

### Funcionalidades Core
- [ ] Ingesta de videos funciona consistentemente
- [ ] Gemini genera clips de calidad
- [ ] Subtítulos se renderizan correctamente
- [ ] Audio normaliza a -14 LUFS
- [ ] Smart crop centra correctamente
- [ ] Scheduler publica sin fallos

### Seguridad
- [ ] Todas las rutas API tienen auth
- [ ] Inputs están validados
- [ ] No hay SQL injection posible
- [ ] Tokens están encriptados
- [ ] CORS configurado correctamente

### Performance
- [ ] Queries DB están optimizadas
- [ ] Assets están comprimidos
- [ ] Caching implementado
- [ ] Lazy loading en frontend

### UX/UI
- [ ] Feedback visual en todas las acciones
- [ ] Loading states implementados
- [ ] Error messages son claros
- [ ] Responsive en mobile

---

## 🎯 SIGUIENTE PASO PARA LA IA

**Tu tarea:**
1. Analiza este documento completo
2. Identifica los 10 problemas más críticos
3. Propón soluciones específicas con código
4. Prioriza por impacto vs esfuerzo
5. Genera un plan de implementación detallado

**Enfócate en:**
- Estabilidad y confiabilidad
- Performance y velocidad
- Experiencia de usuario
- Mantenibilidad del código

---

**Documento generado el:** 2026-02-07  
**Versión de la app:** 0.85  
**Estado:** Production Ready (con mejoras pendientes)
