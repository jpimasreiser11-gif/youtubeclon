import os
import sys
import json
import logging
import subprocess
import shutil
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

import cv2
import numpy as np
try:
    from mediapipe.python.solutions import face_detection as mp_face
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
import textdistance

# Priorizar faster-whisper (CTranslate2, 4x más rápido en CPU)
try:
    from faster_whisper import WhisperModel as FasterWhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
try:
    import google.generativeai as genai
    GEMINI_OLD_AVAILABLE = True
except ImportError:
    GEMINI_OLD_AVAILABLE = False

try:
    from google import genai as genai_new
    GEMINI_NEW_AVAILABLE = True
except ImportError:
    GEMINI_NEW_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

GEMINI_AVAILABLE = GEMINI_OLD_AVAILABLE or GEMINI_NEW_AVAILABLE
try:
    import whisperx
    WHISPERX_AVAILABLE = True
except ImportError:
    WHISPERX_AVAILABLE = False
import yt_dlp
from datetime import timedelta

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SovereignCore")

class ViralEngine:
    def __init__(self, api_key, output_dir="output", ffmpeg_path="ffmpeg", provider="auto", options=None):
        self.output_dir = output_dir
        self.options = options or {}

        # Preset profile for English hybrid mystery workflow.
        profile = str(self.options.get('profile', '')).strip().lower()
        if profile == 'english_mystery_hybrid':
            defaults = {
                'strict_semantic_hooks': True,
                'dynamic_reframe': True,
                'smart_reframe': True,
                'b_roll': True,
                'broll_style': 'split',
                'language': 'en',
            }
            for k, v in defaults.items():
                self.options.setdefault(k, v)

        os.makedirs(output_dir, exist_ok=True)
        
        # AUTO-DISCOVERY: Encontrar FFmpeg automáticamente
        self.ffmpeg_path = self._resolve_ffmpeg(ffmpeg_path)
        
        # Añadir FFmpeg al PATH del sistema para que WhisperX y subprocess lo encuentren
        ffmpeg_dir = os.path.dirname(self.ffmpeg_path)
        if ffmpeg_dir and ffmpeg_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")
            logger.info(f"Añadiendo FFmpeg al PATH: {ffmpeg_dir}")
        
        # Añadir Deno al PATH para resolver YouTube n-challenges (desbloquea formatos HD/4K)
        deno_dir = os.path.join(os.path.expanduser("~"), ".deno", "bin")
        if os.path.isdir(deno_dir) and deno_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = deno_dir + os.pathsep + os.environ.get("PATH", "")
            logger.info(f"Añadiendo Deno al PATH: {deno_dir}")
        
        # NUEVO: Configurar provider (Groq o Gemini)
        self.provider = provider
        if provider == "auto":
            # Auto-detect: verificar que el provider tenga API key configurada
            groq_key = os.getenv("GROQ_API_KEY")
            gemini_key = os.getenv("GEMINI_API_KEY")
            github_models_key = os.getenv("GITHUB_MODELS_TOKEN") or os.getenv("GITHUB_TOKEN")
            
            if GROQ_AVAILABLE and groq_key:
                self.provider = "groq"
                api_key = groq_key
            elif github_models_key:
                self.provider = "github_models"
                api_key = github_models_key
            elif GEMINI_AVAILABLE and gemini_key:
                self.provider = "gemini"
                api_key = gemini_key
            elif GROQ_AVAILABLE:
                self.provider = "groq"
            elif GEMINI_AVAILABLE:
                self.provider = "gemini"
            else:
                raise Exception("No AI provider available. Install 'groq' or 'google-generativeai'")
        
        if self.provider == "groq":
            if not GROQ_AVAILABLE:
                raise Exception("Groq not installed. Run: pip install groq")
            self.client = Groq(api_key=api_key)
            self.model_name = "llama-3.3-70b-versatile"
            logger.info(f"🚀 Usando Groq API con {self.model_name} (FREE - 14,400 requests/día)")
        elif self.provider == "gemini":
            if GEMINI_NEW_AVAILABLE:
                logger.info("Initializing Gemini with NEW 'google-genai' package")
                self.genai_client = genai_new.Client(api_key=api_key)
                self.model_name = "gemini-2.0-flash"
            elif GEMINI_OLD_AVAILABLE:
                logger.info("Initializing Gemini with OLD 'google-generativeai' package")
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash') # Updated from deprecated 1.5-flash
                self.model_name = "gemini-2.0-flash"
            else:
                raise Exception("Gemini package not found. Run: pip install google-genai or google-generativeai")
            logger.info(f"⚠️  Usando Gemini API ({self.model_name})")
        elif self.provider == "github_models":
            self.github_models_token = api_key
            self.model_name = os.getenv("GITHUB_MODELS_NAME", "openai/gpt-4.1-mini")
            logger.info(f"🚀 Usando GitHub Models ({self.model_name})")
        else:
            raise ValueError(f"Provider '{provider}' no soportado. Use 'groq', 'gemini', 'github_models' o 'auto'")
        
        # Cargar Whisper SOLO si WhisperX no está disponible (evita cargar 2 modelos)
        if WHISPERX_AVAILABLE:
            logger.info("WhisperX disponible - se usará para transcripción (Whisper base no cargado)")
            self.whisper_model = None
            self._fw_model = None
            self._whisperx_model = None      # Cache para modelo WhisperX
            self._whisperx_align_model = None # Cache para modelo de alineación
            self._whisperx_align_meta = None
        else:
            self._fw_model = None
            if WHISPER_AVAILABLE:
                logger.info("Cargando modelo Whisper (small)...")
                self.whisper_model = whisper.load_model("small")
            elif FASTER_WHISPER_AVAILABLE:
                logger.info("Whisper no disponible. Usando faster-whisper (CTranslate2)...")
                self.whisper_model = None
            else:
                raise Exception("No hay motor de transcripción disponible. Instala openai-whisper, faster-whisper o whisperx.")
        
        # Inicializar MediaPipe para detección facial
        if MEDIAPIPE_AVAILABLE:
            logger.info("MediaPipe habilitado - usando Smart Crop dinámico")
            self.face_detection = mp_face.FaceDetection(model_selection=1, min_detection_confidence=0.5)
        else:
            logger.warning("MediaPipe no disponible - usando Smart Crop estático (centro)")
            self.face_detection = None
        
        logger.info(f"Using FFmpeg at: {self.ffmpeg_path}")

    @staticmethod
    def _resolve_ffmpeg(ffmpeg_path):
        """Auto-discover FFmpeg binary — critical for yt-dlp merging and audio extraction."""
        
        # 1. Si ya es una ruta absoluta válida, usarla
        if os.path.isfile(ffmpeg_path):
            return os.path.abspath(ffmpeg_path)
        
        # 2. Buscar en ubicaciones conocidas del proyecto
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))  # app/scripts -> app -> project root
        
        known_locations = [
            os.path.join(project_root, "data", "ffmpeg.exe"),
            os.path.join(project_root, "ffmpeg.exe"),
            os.path.join(script_dir, "ffmpeg.exe")
        ]
        
        for loc in known_locations:
            if os.path.isfile(loc):
                logger.info(f"✅ FFmpeg encontrado en: {loc}")
                return os.path.abspath(loc)
        
        # 3. Buscar en el PATH del sistema
        system_ffmpeg = shutil.which("ffmpeg")
        if system_ffmpeg:
            logger.info(f"✅ FFmpeg encontrado en PATH: {system_ffmpeg}")
            return system_ffmpeg
        
        # 4. Último recurso
        logger.warning("⚠️ FFmpeg no encontrado. Usando 'ffmpeg' como comando directo.")
        return "ffmpeg"

    def download_video(self, url):
        """Descarga video en MÁXIMA CALIDAD usando yt-dlp + Deno (hasta 4K)"""
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()
        # Asumiendo self.output_dir es storage/temp/<uuid>
        storage_base = os.path.abspath(os.path.join(self.output_dir, '..', '..'))
        cache_dir = os.path.join(storage_base, 'cache', 'videos')
        os.makedirs(cache_dir, exist_ok=True)
        cached_file = os.path.join(cache_dir, f"{url_hash}.mp4")
        temp_dest = os.path.join(self.output_dir, 'source_video.mp4')
        
        if os.path.exists(cached_file):
            logger.info(f"🟢 [CACHE HIT] Usando video en caché para {url}")
            import shutil
            shutil.copy2(cached_file, temp_dest)
            return temp_dest, "Cached Video"

        logger.info(f"Descargando video en calidad MÁXIMA: {url}")
        
        # FORMATO: Priorizar máxima resolución disponible
        # 1. Mejor video (hasta 4K) + mejor audio, merge con FFmpeg
        # 2. Fallback a mejor formato combinado si merge falla
        format_str = (
            'bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/'
            'bestvideo[height<=2160]+bestaudio/'
            'bestvideo+bestaudio/'
            'best[ext=mp4]/best'
        )
        
        ydl_opts = {
            'format': format_str,
            'outtmpl': cached_file,
            'quiet': True,
            'ffmpeg_location': self.ffmpeg_path,
            'merge_output_format': 'mp4',        # Siempre output MP4
            'no_check_certificates': True,
            'nocheckcertificate': True,
            'no_cache_dir': True,
            'retries': 10,
            'fragment_retries': 10,
            'ignoreerrors': True,
            'concurrent_fragment_downloads': 4,  # 4 fragmentos en paralelo
            # Deno remote-components para resolver n-challenge de YouTube
            # Esto desbloquea TODOS los formatos HD/4K que YouTube oculta
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'android', 'ios'],
                }
            },
            'cookiesfrombrowser': ('chrome',), # FASE 3 - QA Fix: Evasion de Captchas y bloqueos 403
            'socket_timeout': 60,            # FASE 3 - QA Fix: Cortar la conexión si se cuelga (evitar procesos fantasma)
            'extractor_retries': 3           # FASE 3 - QA Fix: Max 3 reintentos para no atascar la cola
        }
        
        # Habilitar remote-components si Deno está disponible (DESHABILITADO POR FALLOS)
        # if shutil.which('deno'):
        #     ydl_opts['remote_components'] = 'ejs:github'
        #     logger.info("   Deno detectado: remote-components habilitado (formatos HD/4K desbloqueados)")
        
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise Exception(f"No se pudo extraer información de {url} (video no disponible)")
                
                filename = ydl.prepare_filename(info)
                title = info.get('title', 'video_corto')
                
                # Log de calidad descargada
                width = info.get('width', '?')
                height = info.get('height', '?')
                fps = info.get('fps', '?')
                vcodec = info.get('vcodec', '?')
                filesize = info.get('filesize_approx', info.get('filesize', 0))
                size_mb = round(filesize / 1024 / 1024, 1) if filesize else '?'
                logger.info(f"   Calidad: {width}x{height} @ {fps}fps ({vcodec}) - {size_mb} MB")
                logger.info(f"   Video descargado a caché: {filename}")
                
                import shutil
                shutil.copy2(filename, temp_dest)
                return temp_dest, title
        except yt_dlp.utils.YoutubeDLError as e:
            if "failed to load cookies" in str(e).lower() or "CookieLoadError" in str(type(e).__name__):
                logger.warning("   ⚠️ No se pudieron cargar cookies de Chrome (navegador abierto o perfil bloqueado). Reintentando SIN cookies...")
                del ydl_opts['cookiesfrombrowser']
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                    info = ydl2.extract_info(url, download=True)
                    if not info:
                        raise Exception(f"No se pudo extraer información de {url} (video no disponible)")
                    
                    filename = ydl2.prepare_filename(info)
                    title = info.get('title', 'video_corto')
                    import shutil
                    shutil.copy2(filename, temp_dest)
                    return temp_dest, title
            else:
                raise e
        except Exception as e:
            logger.error(f"Error descargando {url}: {e}")
            raise



    def detect_face_center(self, video_path, sample_frames=12):
        """
        Detección facial rápida: 12 frames + downscale para velocidad.
        """
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        if not self.options.get('smart_reframe', False):
            logger.info("   Smart Reframe deshabilitado, omitiendo detección facial.")
            cap.release()
            return width // 2, width, height
            
        logger.info(f"Detectando posición facial ({sample_frames} frames)...")
        
        # Inicializar Haar Cascade como fallback
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        detection_method = "None"
        if self.face_detection:
            detection_method = "MediaPipe"
        elif not face_cascade.empty():
            detection_method = "Haar Cascade"
        else:
            logger.warning("⚠️ Ningún método de detección disponible, usando centro.")
            cap.release()
            return width // 2, width, height

        logger.info(f"   Utilizando método: {detection_method}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_indices = np.linspace(0, total_frames - 1, sample_frames, dtype=int)
        
        face_centers_x = []
        
        for frame_idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            if not ret: continue
            
            # Downscale para procesamiento más rápido (detectar caras en 480px)
            scale = 480.0 / max(frame.shape[1], 1)
            if scale < 1.0:
                small_frame = cv2.resize(frame, None, fx=scale, fy=scale)
            else:
                small_frame = frame
            
            if detection_method == "MediaPipe":
                rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                results = self.face_detection.process(rgb_frame)
                if results.detections:
                    bbox = results.detections[0].location_data.relative_bounding_box
                    center_x = int((bbox.xmin + bbox.width / 2) * width)
                    face_centers_x.append(center_x)
            else: # Haar Cascade
                gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                if len(faces) > 0:
                    (x, y, w, h) = faces[0]
                    center_x = int((x + w // 2) / scale)  # Escalar de vuelta a resolución original
                    face_centers_x.append(center_x)
        
        cap.release()
        
        if face_centers_x:
            avg_center_x = int(np.mean(face_centers_x))
            logger.info(f"✅ Seguimiento facial completado ({detection_method}): X={avg_center_x} px")
            return avg_center_x, width, height
        else:
            logger.warning("⚠️ No se detectaron caras, usando centro del frame")
            return width // 2, width, height

    def extract_audio(self, video_path):
        """Extrae audio como WAV 16kHz mono — formato óptimo para Whisper (sin re-encoding)"""
        audio_path = video_path.rsplit('.', 1)[0] + ".wav"
        logger.info(f"Extrayendo audio (WAV 16kHz)...")
        
        cmd = [
            self.ffmpeg_path, '-y',
            '-i', video_path,
            '-vn',
            '-acodec', 'pcm_s16le',  # WAV sin compresión — instantáneo
            '-ar', '16000',           # 16kHz — formato nativo de Whisper
            '-ac', '1',               # Mono — reduce datos a la mitad
            audio_path
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            logger.info("   ✓ Audio extraído correctamente")
            return audio_path
        except subprocess.CalledProcessError as e:
            logger.error(f"   ❌ Error extrayendo audio: {e.stderr.decode()}")
            return video_path # Fallback al video si falla

    def transcribe_precise(self, file_path):
        """
        Transcribe y obtiene timestamps a nivel de PALABRA.
        Usa WhisperX para ALINEACIÓN FORZADA si está disponible (estándar 2025).
        """
        if WHISPERX_AVAILABLE:
            logger.info(f"Usando WhisperX para Alineacion Forzada (Fiel al audio)")
            device = "cpu"
            audio = whisperx.load_audio(file_path)
            
            # CACHE: Reutilizar modelo WhisperX entre llamadas (~10s ahorrados)
            if self._whisperx_model is None:
                logger.info("   Cargando modelo WhisperX (primera vez)...")
                self._whisperx_model = whisperx.load_model("small", device, compute_type="int8")
            
            result = self._whisperx_model.transcribe(audio, batch_size=16)
            
            # CACHE: Reutilizar modelo de alineación
            detected_lang = result["language"]
            if self._whisperx_align_model is None:
                logger.info(f"   Cargando modelo de alineación para '{detected_lang}' (primera vez)...")
                self._whisperx_align_model, self._whisperx_align_meta = whisperx.load_align_model(
                    language_code=detected_lang, device=device
                )
            result = whisperx.align(result["segments"], self._whisperx_align_model, self._whisperx_align_meta, audio, device, return_char_alignments=False)
            
            all_words = []
            for segment in result['segments']:
                for word in segment['words']:
                    if 'start' in word and 'end' in word:
                        all_words.append({
                            'word': word['word'].strip(),
                            'start': word['start'],
                            'end': word['end'],
                            'confidence': word.get('score', 0)
                        })
            
            full_text = " ".join([s['text'] for s in result['segments']])
            return all_words, full_text

        # FALLBACK: faster-whisper (CTranslate2, 4x más rápido que openai-whisper)
        if FASTER_WHISPER_AVAILABLE:
            logger.info("Transcribiendo con faster-whisper (CTranslate2)...")

            # Limitar hilos para evitar bloqueos en Windows/OpenMP.
            os.environ["OMP_NUM_THREADS"] = "4"
            os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

            if not hasattr(self, '_fw_model') or self._fw_model is None:
                self._fw_model = FasterWhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4, num_workers=1)

            segments, info = self._fw_model.transcribe(file_path, word_timestamps=True)

            all_words = []
            full_text_parts = []
            for segment in segments:
                full_text_parts.append(segment.text)
                if segment.words:
                    for word in segment.words:
                        all_words.append({
                            'word': word.word.strip(),
                            'start': word.start,
                            'end': word.end,
                            'confidence': word.probability
                        })

            return all_words, " ".join(full_text_parts)

        # FALLBACK 2: Whisper estándar (más lento)
        if not WHISPER_AVAILABLE:
            raise Exception("No hay motor de transcripción disponible. Instala: pip install faster-whisper")
        logger.info("Transcribiendo con Whisper estándar (más lento)...")
        if self.whisper_model is None:
            self.whisper_model = whisper.load_model("small")
        try:
            result = self.whisper_model.transcribe(file_path, word_timestamps=True, fp16=False)
        except Exception as e:
            logger.error(f"Error en transcripción Whisper: {e}")
            raise
        
        all_words = []
        for segment in result['segments']:
            for word in segment['words']:
                all_words.append({
                    'word': word['word'].strip(),
                    'start': word['start'],
                    'end': word['end'],
                    'confidence': word.get('probability', 0)
                })
        
        full_text = result['text']
        return all_words, full_text

    def analyze_virality(self, full_text):
        """Usa Gemini/Groq para encontrar los momentos virales con prompt optimizado y chunking"""
        
        # Límite de caracteres por chunk (12k chars ~= 3k tokens)
        # Groq Free Tier LLaMA 3.3: Límite 6,000 TPM.
        # 3k (prompt) + 1.5k (response reserve) = 4.5k < 6k. Safe.
        CHUNK_SIZE = 12000
        
        if len(full_text) <= CHUNK_SIZE:
            logger.info(f"📜 Texto corto ({len(full_text)} chars). Procesando en una sola llamada.")
            return self._analyze_chunk(full_text)
            
        logger.info(f"📜 Texto largo ({len(full_text)} chars). Dividiendo en chunks para evitar límites de API...")
        # Dividir transcript en chunks
        chunks = [full_text[i:i+CHUNK_SIZE] for i in range(0, len(full_text), CHUNK_SIZE)]
        
        all_clips = []
        for i, chunk in enumerate(chunks):
            logger.info(f"   🔄 Procesando parte {i+1}/{len(chunks)} ({len(chunk)} chars)...")
            try:
                # Añadir contexto ligero si es posible, pero por ahora chunk puro
                chunk_clips = self._analyze_chunk(chunk)
                if chunk_clips:
                    # Ajustar scores o filtrar si necesario
                    all_clips.extend(chunk_clips)
                
                # Pausa para respetar Rate Limits (especialmente TPM: 6k/min en Free Tier)
                # Un chunk de 15k chars son ~3.5k tokens. Solo podemos procesar ~1.5 chunks/min.
                logger.info("   ⏳ Esperando 20s para respetar límites de Groq...")
                time.sleep(20) 
            except Exception as e:
                logger.error(f"   ❌ Error procesando chunk {i+1}: {e}")
                # Continuar con siguientes chunks
                
        logger.info(f"✅ Análisis completado. Total clips encontrados: {len(all_clips)}")
        return all_clips

    def _analyze_chunk(self, text_chunk):
        """Procesa un fragmento de texto con la API seleccionada (lógica original)"""

        lang_mode = str(self.options.get('language', 'auto')).strip().lower()
        if lang_mode == 'en':
            system_prompt = """
            You are an elite short-video editor for YouTube Shorts and TikTok.

            STRICT OBJECTIVE:
            Return ONLY 30-60 second clips with full narrative shape:
            1) Strong hook in first 3 seconds.
            2) Fast, clear development.
            3) Explicit payoff at the end.

            CRITICAL RULES:
            - No cuts by loudness. Select by semantic meaning.
            - start_text and end_text must be exact transcript fragments.
            - Clip must be self-contained and understandable without external context.
            - No sentence cut in half.

            OUTPUT FORMAT (JSON only):
            [
                {
                    "start_text": "exact phrase",
                    "end_text": "exact phrase",
                    "virality_metrics": {
                        "hook_power": 9,
                        "emotional_impact": 8,
                        "value_density": 9,
                        "trend_potential": 8
                    },
                    "category": "Educational/Entertainment/Motivational",
                    "hook": "one-line hook description",
                    "payoff": "one-line payoff description",
                    "reason": "why it can go viral (max 20 words)",
                    "title": "UPPERCASE click title max 50 chars",
                    "description": "retention-first description max 150 chars",
                    "hashtags": "3-5 hashtags",
                    "broll_inserts": [
                        {
                            "keyword": "1-2 english words",
                            "start_text": "exact phrase",
                            "end_text": "exact phrase"
                        }
                    ]
                }
            ]
            """
        else:
            system_prompt = """
            Eres un editor ELITE de videos (YouTube/TikTok/Reels) especializado en retención.

            OBJETIVO ESTRICTO:
            Selecciona SOLO clips de 30 a 60 segundos con estructura narrativa completa:
            1) Gancho polemico en los primeros 3 segundos.
            2) Desarrollo rapido y claro.
            3) Remate/payoff explicitamente entendible al final.

            CRITERIOS CRITICOS:
            - El clip debe ser autosuficiente, con contexto completo.
            - Prohibido cortar frases a mitad o terminar sin cierre.
            - No seleccionar segmentos por volumen o gritos: prioriza semantica y narrativa.
            - start_text y end_text deben existir literalmente en el transcript.

            FORMATO DE SALIDA (JSON puro, sin markdown):
            [
                {
                    "start_text": "frase EXACTA de inicio (primeras 5-8 palabras)",
                    "end_text": "frase EXACTA de cierre (últimas 5-8 palabras)",
                    "virality_metrics": {
                        "hook_power": 9,
                        "emotional_impact": 8,
                        "value_density": 9,
                        "trend_potential": 8
                    },
                    "category": "Educational/Entertainment/Motivational",
                    "hook": "Describe el gancho en 1 línea",
                    "payoff": "Describe el cierre en 1 línea",
                    "reason": "Por qué explotaría en redes (máx 20 palabras)",
                    "title": "Título CLICKBAIT en MAYÚSCULAS (max 50 chars)",
                    "description": "Descripción optimizada para retención (máx 150 caracteres)",
                    "hashtags": "3-5 hashtags virales relevantes (ej. #crypto #finance #growth)",
                    "broll_inserts": [
                        {
                            "keyword": "1-2 palabras en INGLÉS buscando en Pexels (ej. money, running, nature)",
                            "start_text": "frase EXACTA donde debe entrar el clip de apoyo",
                            "end_text": "frase EXACTA donde debe ocultarse"
                        }
                    ]
                }
            ]

            IMPORTANTE:
            - Duracion final esperada: 30-60s.
            - Puntúa las 4 virality_metrics de 1 al 10 con la máxima exigencia.
            - Máximo 5 clips
            - start_text y end_text (tanto del clip principal como de los b-rolls) deben coincidir PALABRA POR PALABRA con el transcript original.
            - Genera 1 o 2 broll_inserts por clip si ayudan a enriquecer visualmente el tema. Si no hace falta, envía el array vacío [].
            """

        # CRITICAL FIX: Manejo robusto de rate limit con reintentos extensos
        max_retries = 5
        base_delay = 15

        for attempt in range(max_retries):
            try:
                # Soportar múltiples providers con FALLBACK AUTOMÁTICO
                if self.provider == "groq":
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"TRANSCRIPT FRAGMENT:\n{text_chunk}"}
                            ],
                            temperature=0.7,
                            max_tokens=1500
                        )
                        response_text = response.choices[0].message.content
                    except Exception as groq_err:
                        # Si Groq falla (403 Forbidden, Rate Limit, etc), intentar con Gemini si está disponible
                        if GEMINI_AVAILABLE:
                            logger.warning(f"⚠️ Groq falló ({groq_err}). Intentando Fallback a Gemini...")
                            if GEMINI_NEW_AVAILABLE and hasattr(self, 'genai_client'):
                                response = self.genai_client.models.generate_content(
                                    model="gemini-2.0-flash",
                                    contents=f"{system_prompt}\n\nTRANSCRIPT FRAGMENT:\n{text_chunk}"
                                )
                                response_text = response.text
                            else:
                                # Usar modelo configurado o fallback
                                model = getattr(self, 'model', None) or genai.GenerativeModel('gemini-2.0-flash')
                                response = model.generate_content(f"{system_prompt}\n\nTRANSCRIPT FRAGMENT:\n{text_chunk}")
                                response_text = response.text
                        else:
                            raise groq_err
                elif self.provider == "github_models":
                    endpoint = os.getenv("GITHUB_MODELS_ENDPOINT", "https://models.inference.ai.azure.com/chat/completions")
                    headers = {
                        "Authorization": f"Bearer {self.github_models_token}",
                        "Content-Type": "application/json",
                    }
                    payload = {
                        "model": self.model_name,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"TRANSCRIPT FRAGMENT:\n{text_chunk}"}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1500,
                    }
                    response = requests.post(endpoint, headers=headers, json=payload, timeout=120)
                    response.raise_for_status()
                    response_data = response.json() or {}
                    choices = response_data.get("choices") or []
                    if not choices:
                        raise RuntimeError("GitHub Models returned empty choices")
                    response_text = ((choices[0] or {}).get("message") or {}).get("content", "")
                else:  # gemini
                    if GEMINI_NEW_AVAILABLE and hasattr(self, 'genai_client'):
                        response = self.genai_client.models.generate_content(
                            model=self.model_name,
                            contents=f"{system_prompt}\n\nTRANSCRIPT FRAGMENT:\n{text_chunk}"
                        )
                        response_text = response.text
                    else:
                        response = self.model.generate_content(f"{system_prompt}\n\nTRANSCRIPT FRAGMENT:\n{text_chunk}")
                        response_text = response.text

                # Parse JSON (común para ambos providers)
                try:
                    import re
                    # Robust extraction of JSON array using regex
                    json_match = re.search(r'(\[.*\])', response_text, re.DOTALL)
                    if json_match:
                        clean_json = json_match.group(1)
                    else:
                        clean_json = response_text.replace('```json', '').replace('```', '').strip()

                    clips_metadata = json.loads(clean_json)
                    logger.info(f"✅ {self.provider.upper()} encontró {len(clips_metadata)} clips en este chunk")

                    # Rate-limit delay (reducido: solo necesario entre chunks consecutivos)
                    delay = 3 if self.provider == "groq" else 2
                    logger.info(f"   Pausa {delay}s anti rate-limit...")
                    time.sleep(delay)

                    return clips_metadata
                except json.JSONDecodeError as je:
                    logger.warning(f"   ⚠️ Malformed JSON en intento {attempt + 1}: {je}")
                    if attempt < max_retries - 1:
                        logger.info("   ⏳ Reintentando chunk de texto (prompting de nuevo)...")
                        continue
                    else:
                        logger.error(f"Respuesta Raw Final: {response_text[:500]}")
                        return []
                except Exception as e:
                    logger.error(f"Error inesperado en JSON.loads: {e}")
                    return []

            except Exception as api_error:
                error_msg = str(api_error)

                # Detectar error 429 específicamente
                if "429" in error_msg or "ResourceExhausted" in error_msg or "quota" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)  # Backoff exponencial: 15s, 30s, 60s, 120s...
                        logger.warning(f"⚠️  Rate limit alcanzado. Reintentando en {wait_time}s... (intento {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"❌ Rate limit persistente después de {max_retries} intentos.")
                        raise Exception("Rate limit de API excedido.")
                else:
                    # Otro tipo de error - no reintentar
                    logger.error(f"Error en API: {api_error}")
                    raise

        return []


    def snap_to_word_boundaries(self, all_words, start_phrase, end_phrase):
        """
        ALINEACIÓN FORZADA: Busca la frase en Whisper y ajusta a palabra exacta
        """
        words_list = [w['word'].lower() for w in all_words]
        start_tokens = start_phrase.lower().split()
        end_tokens = end_phrase.lower().split()
        
        # Buscar inicio
        best_start_idx = -1
        best_start_score = 0
        window_size = len(start_tokens)
        
        for i in range(len(words_list) - window_size):
            segment = words_list[i : i + window_size]
            score = textdistance.jaccard(segment, start_tokens)
            if score > best_start_score and score > 0.5:
                best_start_score = score
                best_start_idx = i

        # Buscar final
        best_end_idx = -1
        best_end_score = 0
        search_start = best_start_idx + 1 if best_start_idx != -1 else 0
        window_size_end = len(end_tokens)
        
        for i in range(search_start, len(words_list) - window_size_end):
            segment = words_list[i : i + window_size_end]
            score = textdistance.jaccard(segment, end_tokens)
            if score > best_end_score and score > 0.5:
                best_end_score = score
                best_end_idx = i + window_size_end - 1

        if best_start_idx != -1 and best_end_idx != -1:
            start_time = max(0, all_words[best_start_idx]['start'])
            end_time = all_words[best_end_idx]['end']
            clip_words = all_words[best_start_idx : best_end_idx + 1]
            
            logger.info(f"   Snap: {start_time:.2f}s - {end_time:.2f}s ({len(clip_words)} palabras)")
            return start_time, end_time, clip_words
        
        return None, None, None

    def generate_karaoke_subtitles(self, clip_words, output_filename="subtitles.ass"):
        """
        Genera subtítulos DINÁMICOS estilo Opus/Hormozi con efecto karaoke avanzado.
        Efectos: BOUNCE (Pop) y SHINE (Border Glow).
        """
        logger.info(f"Generando subtítulos con efecto BOUNCE & SHINE (2026 Style)...")
        
        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 1

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,120,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,6,4,2,40,40,550,1
Style: Highlight,Arial Black,125,&H0000E5FF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,8,4,2,40,40,550,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        events = []
        words_per_line = 3
        
        for i in range(0, len(clip_words), words_per_line):
            chunk = clip_words[i:i+words_per_line]
            chunk_start = chunk[0]['start']
            chunk_end = chunk[-1]['end']
            
            # Línea base (todas las palabras en blanco/dimmed)
            base_text = " ".join([w['word'].upper() for w in chunk])
            line = f"Dialogue: 0,{self._format_time(chunk_start)},{self._format_time(chunk_end)},Default,,0,0,0,,{base_text}"
            events.append(line)
            
            # Highlights individuales con BOUNCE & SHINE (amarillo neón y verde vibrante alternos)
            for j, word in enumerate(chunk):
                start_f = self._format_time(word['start'])
                end_f = self._format_time(word['end'])
                
                duration_ms = int((word['end'] - word['start']) * 1000)
                t_pop = min(60, int(duration_ms * 0.4))
                
                # Alternar colores para dinamismo
                colores = ["&H0000E5FF&", "&H004AFF00&"] # Amarillo Neón / Verde Clásico
                color_bg = colores[j % 2]
                
                anim = f"{{\\c{color_bg}\\3c{color_bg}\\bord8\\t(0,{t_pop},\\fscx115\\fscy115\\bord12)\\t({t_pop},{duration_ms},\\fscx100\\fscy100\\bord8)}}"
                
                line = f"Dialogue: 1,{start_f},{end_f},Highlight,,0,0,0,,{anim}{word['word'].upper()}"
                events.append(line)
        
        with open(output_filename, "w", encoding='utf-8') as f:
            f.write(header + "\n".join(events))
        
        return output_filename

    def _format_time(self, seconds):
        """Convierte segundos a formato ASS (H:MM:SS.cs)"""
        td = timedelta(seconds=seconds)
        hours, remainder = divmod(td.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        centiseconds = int(td.microseconds / 10000)
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

    def process_video_with_smart_crop(self, source_path, start, end, ass_path, output_path, face_center_x=None, source_width=None, broll_data=None):
        """
        Renderiza clip con Smart Crop centrado en la cara + Subtítulos quemados
        """
        import subprocess as sp
        logger.info(f"Renderizando clip: {output_path}")
        
        duration = end - start
        use_dynamic_reframe = bool(self.options.get('smart_reframe', False) and self.options.get('dynamic_reframe', True))
        dynamic_video_path = None
        
        # Si tenemos detección facial, usar esa coordenada; sino centro estático
        # ESTRATEGIA: 
        # - Videos grandes (≥1080px ancho): Crop 9:16 centrado en cara
        # - Videos pequeños (<1080px ancho): Scale+Pad a 1080x1920
        
        if use_dynamic_reframe:
            try:
                from auto_reframe import render_dynamic_reframe

                dynamic_video_path = os.path.join(self.output_dir, f"dynamic_reframe_{int(start * 1000)}_{int(end * 1000)}.mp4")
                logger.info("   Smart Reframe Dinamico: seguimiento de nariz/hablante activo")
                render_dynamic_reframe(
                    input_video=source_path,
                    output_video=dynamic_video_path,
                    start_time=start,
                    duration=duration,
                    target_width=1080,
                    target_height=1920,
                )
                vf_base = "scale=1080:1920"
            except Exception as reframe_err:
                logger.warning(f"   Auto-reframe dinamico fallo ({reframe_err}). Usando crop estatico.")
                use_dynamic_reframe = False

        if not use_dynamic_reframe:
            if source_width >= 1080:
                # Videos HD: usar crop tradicional centrado en cara
                if face_center_x and source_width:
                    crop_width = min(int(source_width * (9/16)), source_width)
                    crop_x = max(0, min(face_center_x - crop_width // 2, source_width - crop_width))
                    vf_base = f"crop={crop_width}:ih:{crop_x}:0,scale=1080:1920"
                    logger.info(f"   Smart Crop HD: ancho={crop_width}px, x={crop_x}px (cara en {face_center_x}px)")
                else:
                    vf_base = "crop=ih*(9/16):ih:(iw-ow)/2:0,scale=1080:1920"
                    logger.info("   Usando crop estatico HD (sin deteccion facial)")
            else:
                # Videos pequeños: escalar y rellenar a 1080x1920
                vf_base = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"
                logger.info(f"   Video pequeño ({source_width}px) -> Scale+Pad a 1080x1920")
        
        # ------------------------------------------------------------------
        # FFMPEG PIpeline Construction (Base + B-Roll Overlays)
        # ------------------------------------------------------------------
        
        if use_dynamic_reframe and dynamic_video_path and os.path.exists(dynamic_video_path):
            ffmpeg_inputs = ['-i', dynamic_video_path, '-ss', str(start), '-t', str(duration), '-i', source_path]
            audio_map = '1:a'
        else:
            ffmpeg_inputs = ['-ss', str(start), '-t', str(duration), '-i', source_path]
            audio_map = '0:a'
        
        # Prepare ASS path for FFmpeg (escape backslashes for Windows)
        safe_ass_path = ass_path.replace('\\', '/').replace(':', '\\:')
        
        if not broll_data:
            filter_args = ['-vf', f"{vf_base},ass='{safe_ass_path}'", '-map', '0:v', '-map', audio_map]
        else:
            # Burn ASS subtitles into the very last layer
            filter_complex = f"[0:v]{vf_base}[base];"
            last_layer = "base"
            broll_input_offset = 2 if (use_dynamic_reframe and dynamic_video_path and os.path.exists(dynamic_video_path)) else 1
            
            for i, br in enumerate(broll_data):
                # 1..N correspond to broll inputs because 0 is the main video
                in_idx = i + broll_input_offset
                ffmpeg_inputs.extend(['-i', br['path']])
                
                br_start = br['start']
                br_end = br['end']
                br_duration = br_end - br_start
                
                # B-Roll Opus-killer floating picture-in-picture effect
                frames = int(br_duration * 30) 
                broll_mode = (br.get('mode') or 'overlay').lower()
                
                if broll_mode == 'split':
                    # Split-screen: mitad inferior para convertir el clip en contenido visualmente nuevo.
                    fc_broll = (
                        f"[{in_idx}:v]scale=1080:960:force_original_aspect_ratio=increase,"
                        f"crop=1080:960,setsar=1,format=yuv420p,"
                        f"zoompan=z='min(pzoom+0.0012,1.10)':d={frames}:s=1080x960,"
                        f"setpts=PTS-STARTPTS+{br_start}/TB[broll_{in_idx}];"
                    )
                else:
                    # Overlay mode (PiP)
                    fc_broll = (
                        f"[{in_idx}:v]scale=960:540:force_original_aspect_ratio=increase,"
                        f"crop=960:540,setsar=1,format=yuv420p,"
                        f"zoompan=z='min(pzoom+0.0015,1.15)':d={frames}:s=960x540,"
                        f"pad=980:560:10:10:white,"
                        f"setpts=PTS-STARTPTS+{br_start}/TB[broll_{in_idx}];"
                    )
                filter_complex += fc_broll
                
                if broll_mode == 'split':
                    split_base = f"[{last_layer}]crop=iw:960:0:0,setsar=1[top_{in_idx}];"
                    split_stack = f"[top_{in_idx}][broll_{in_idx}]vstack=inputs=2[layer_{in_idx}_raw];"
                    split_enable = (
                        f"[{last_layer}][layer_{in_idx}_raw]overlay=0:0:"
                        f"enable='between(t,{br_start},{br_end})'[layer_{in_idx}];"
                    )
                    filter_complex += split_base + split_stack + split_enable
                else:
                    # Overlay settings - (W-w)/2 centra horizontalmente, y=150 ubica en tercio superior real
                    fc_overlay = f"[{last_layer}][broll_{in_idx}]overlay=x=(W-w)/2:y=150:enable='between(t,{br_start},{br_end})'[layer_{in_idx}];"
                    filter_complex += fc_overlay
                last_layer = f"layer_{in_idx}"
            
            # Apply subtitles to the final composited layer
            final_filter = f"[{last_layer}]ass='{safe_ass_path}'[v]"
            filter_complex += final_filter
            filter_args = ['-filter_complex', filter_complex, '-map', '[v]', '-map', audio_map]

        # Comando FFmpeg final multi-threading
        cmd = [self.ffmpeg_path, '-y'] + ffmpeg_inputs + filter_args + [
            '-c:v', 'libx264', 
            '-preset', 'fast',         # Fast preset for optimal speed vs quality ratio on CPU
            '-crf', '18',              # VISUALLY LOSSLESS QUALITY
            '-profile:v', 'high',      # High profile for social media
            '-pix_fmt', 'yuv420p',     # Required pixel format for TikTok/IG compatibility
            '-threads', '0',           # Usar todos los cores del CPU
            '-c:a', 'aac', 
            '-ab', '192k',             # High quality audio
            '-af', 'acompressor,loudnorm=I=-14:TP=-1.5:LRA=1', # Compresion tipo radio/TikTok
            output_path
        ]
        
        try:
            sp.run(cmd, check=True, stdout=sp.DEVNULL, stderr=sp.PIPE)
            logger.info(f"   ✅ Clip renderizado exitosamente")
        except sp.CalledProcessError as e:
            logger.error(f"   ❌ Error en FFmpeg ({self.ffmpeg_path}): {e.stderr.decode() if e.stderr else 'Unknown'}")
            raise
        finally:
            if dynamic_video_path and os.path.exists(dynamic_video_path):
                try:
                    os.remove(dynamic_video_path)
                except Exception:
                    pass

    def run_pipeline(self, youtube_url, on_progress=None):
        """
        Pipeline completo: Download → Whisper → Gemini → Face Detection → Render
        Soporta opciones: audio_pro, smart_reframe, clean_speech, etc.
        """
        logger.info(f"🚀 Iniciando Pipeline 2026 con opciones: {self.options}")
        
        def report(stage, percent):
            if on_progress:
                on_progress(stage, percent)
            logger.info(f"Progress: [{percent}%] {stage}")

        # 1. Ingesta
        report("Descargando video...", 10)
        video_path, title = self.download_video(youtube_url)
        report("Video descargado", 20)
        
        # 2. Deteccion facial + Extraccion audio EN PARALELO
        report("Analizando video (cara + audio en paralelo)...", 25)
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            face_future = executor.submit(self.detect_face_center, video_path)
            audio_future = executor.submit(self.extract_audio, video_path)
            
            face_center_x, source_width, source_height = face_future.result()
            audio_path = audio_future.result()
            
        if self.options.get('audio_pro', False):
            report("Mejorando audio (Studio Quality)...", 30)
            logger.info("🎬 [Enterprise] Applying Audio Pro Normalization...")
            restored_audio = os.path.join(self.output_dir, "restored_audio.mp3")
            restore_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'scripts', 'audio_processor.py'))
            
            try:
                sp.run([sys.executable, restore_script, '--input', audio_path, '--output', restored_audio], check=True)
                logger.info(f"✅ Audio restored and normalized: {restored_audio}")
                
                # Merge restored audio back into a master video for quality consistency during crops
                master_video = os.path.join(self.output_dir, "source_video_master.mp4")
                merge_cmd = [
                    self.ffmpeg_path, "-y",
                    "-i", video_path,
                    "-i", restored_audio,
                    "-map", "0:v",
                    "-map", "1:a",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    master_video
                ]
                sp.run(merge_cmd, check=True)
                
                video_path = master_video
                audio_path = restored_audio
            except Exception as e:
                logger.error(f"⚠️ Audio restoration failed: {e}. Falling back to original audio.")
        
        report(f"Seguimiento configurado (X:{face_center_x}px) + Audio listo", 35)
        
        report("Transcribiendo audio (Whisper)...", 40)
        
        # --- NUEVO: Ticker de progreso para Whisper ---
        import threading
        
        whisper_done = False
        def whisper_progress_ticker():
            current_pct = 40
            max_pct = 69  # Tope justo antes de "Analizando viralidad"
            # Velocidad adaptativa: empieza rápido (8s/%) y desacelera progresivamente.
            # Esto cubre desde videos cortos (2 min) hasta muy largos (30+ min)
            # sin que la barra JAMÁS se congele.
            while not whisper_done and current_pct < max_pct:
                # Velocidad variable: más lento cuanto más avanzado
                if current_pct < 55:
                    wait_per_step = 8   # Rápido al principio
                elif current_pct < 63:
                    wait_per_step = 15  # Medio
                else:
                    wait_per_step = 30  # Lento al final (da margen a videos largos)
                
                for _ in range(wait_per_step):
                    if whisper_done: break
                    time.sleep(1)
                if not whisper_done:
                    current_pct += 1
                    report("Transcribiendo audio (Whisper)...", current_pct)
                    
        ticker_thread = threading.Thread(target=whisper_progress_ticker)
        ticker_thread.daemon = True
        ticker_thread.start()
        
        try:
            import hashlib
            url_hash = hashlib.md5(youtube_url.encode()).hexdigest()
            storage_base = os.path.abspath(os.path.join(self.output_dir, '..', '..'))
            cache_dir = os.path.join(storage_base, 'cache', 'transcripts')
            os.makedirs(cache_dir, exist_ok=True)
            cached_transcript = os.path.join(cache_dir, f"{url_hash}.json")
            
            if os.path.exists(cached_transcript):
                logger.info(f"🟢 [CACHE HIT] Usando transcripción en caché para {youtube_url}")
                with open(cached_transcript, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    words = data['words']
                    full_text = data['full_text']
            else:
                words, full_text = self.transcribe_precise(audio_path)
                with open(cached_transcript, 'w', encoding='utf-8') as f:
                    json.dump({'words': words, 'full_text': full_text}, f)
        finally:
            whisper_done = True
            ticker_thread.join(timeout=1.0)
        # ----------------------------------------------
        
        # Limpiar audio temporal si se creó
        if audio_path != video_path and os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass
                
        report("Transcripción completada", 60)
        
        # 4. Análisis de viralidad con Gemini
        report("Analizando viralidad (Gemini AI)...", 70)
        viral_candidates = self.analyze_virality(full_text)
        
        results = []
        
        # 5. Pre-pass: Validate and Tournament Scoring
        logger.info(f"Se encontraron {len(viral_candidates)} candidatos virales. Iniciando Torneo Virality...")
        
        valid_candidates = []
        for clip in viral_candidates:
            # Snap-to-word boundaries para calcular el WPM y check de duración
            start, end, clip_words = self.snap_to_word_boundaries(
                words, clip['start_text'], clip['end_text']
            )
            if not start:
                continue

            duration = end - start
            strict_semantic = bool(self.options.get('strict_semantic_hooks', True))
            if strict_semantic:
                if duration < 30.0 or duration > 60.0:
                    continue
            elif duration < 20.0 or duration > 240.0:
                continue

            hook_txt = str(clip.get('hook', '') or '').strip()
            payoff_txt = str(clip.get('payoff', '') or '').strip()
            if strict_semantic and (len(hook_txt.split()) < 4 or len(payoff_txt.split()) < 4):
                continue
                
            clip['_start'] = start
            clip['_end'] = end
            clip['_clip_words'] = clip_words
            clip['_duration'] = duration
            
            # WPM Analysis
            word_count = len(clip_words)
            wpm = (word_count / duration) * 60 if duration > 0 else 0
            clip['wpm'] = wpm
            
            # AI Base Score
            metrics = clip.get('virality_metrics', {})
            if isinstance(metrics, dict) and metrics:
                base = sum([
                    metrics.get('hook_power', 7),
                    metrics.get('emotional_impact', 7),
                    metrics.get('value_density', 7),
                    metrics.get('trend_potential', 7)
                ]) / 40.0 * 100
            else:
                base = 75.0
                
            # WPM Bonus
            pacing_bonus = 0
            if 140 <= wpm <= 175: pacing_bonus = 15
            elif 120 <= wpm < 140 or 175 < wpm <= 190: pacing_bonus = 5
            else: pacing_bonus = -10
            
            # Hook short bonus
            hook_bonus = 5 if len(clip.get('hook', '').split()) <= 12 else 0

            clip['_raw_score'] = min(max(base + pacing_bonus + hook_bonus, 10), 99)
            valid_candidates.append(clip)
            
        # Ejecutar el Torneo
        valid_candidates.sort(key=lambda x: x.get('_raw_score', 0), reverse=True)
        if valid_candidates:
            best_raw = valid_candidates[0].get('_raw_score', 0)
            for i, clip in enumerate(valid_candidates):
                normalized = (clip['_raw_score'] / best_raw) * 96 if best_raw > 0 else clip['_raw_score']
                if i == 0: normalized += 3
                elif i == 1: normalized += 1
                
                # Asignar la nota real en la metadata
                clip['virality_score'] = int(min(max(normalized, 10), 99))
        
        # 6. Procesamiento de clips EN PARALELO
        total_clips = len(valid_candidates)
        logger.info(f"Total clips validados para render: {total_clips}")
        
        def render_clip_task(i, clip):
            clip_start_time = time.time()
            logger.info(f"\n🎬 Iniciando render paralelo - Clip {i+1}/{total_clips}: {clip['title']}")
            
            # Recuperar valores del pre-pass
            start = clip['_start']
            end = clip['_end']
            duration = clip['_duration']
            clip_words = clip['_clip_words']
                
            # Procesar B-Roll Inserts only if enabled
            broll_data = []
            if self.options.get('b_roll', False):
                from broll_manager import BRollManager
                broll_manager = BRollManager(api_key=os.getenv("PEXELS_API_KEY"))
                broll_style = (self.options.get('broll_style') or 'split').lower()
                generated_inserts = list(clip.get('broll_inserts', []) or [])

                if not generated_inserts:
                    clip_text = " ".join([w.get('word', '') for w in clip_words if isinstance(w, dict)])
                    auto_keywords = broll_manager.extract_keywords_from_text(clip_text, limit=2)
                    if auto_keywords:
                        seg_len = max(2.5, min(5.0, duration / 4.0))
                        t0 = max(0.8, min(3.0, duration * 0.15))
                        for kw_i, kw in enumerate(auto_keywords):
                            s = min(duration - 1.0, t0 + (kw_i * (seg_len + 1.8)))
                            e = min(duration - 0.2, s + seg_len)
                            if e > s:
                                broll_data.append({
                                    'path': broll_manager.fetch_video(kw, self.project_id if hasattr(self, 'project_id') else "temp", i + kw_i),
                                    'start': s,
                                    'end': e,
                                    'mode': broll_style,
                                })
                        broll_data = [b for b in broll_data if b.get('path')]
                
                for b_idx, b_insert in enumerate(generated_inserts):
                    b_start, b_end, b_words = self.snap_to_word_boundaries(
                        words, b_insert['start_text'], b_insert['end_text']
                    )
                    if b_start and b_end:
                        b_path = broll_manager.fetch_video(b_insert['keyword'], self.project_id if hasattr(self, 'project_id') else "temp", i)
                        if b_path:
                            rel_start = b_start - start
                            rel_end = b_end - start
                            
                            if rel_start >= 0 and rel_end <= (end - start):
                                broll_data.append({
                                    'path': b_path,
                                    'start': rel_start,
                                    'end': rel_end,
                                    'mode': broll_style,
                                })

            # Generar subtítulos karaoke
            ass_file = os.path.join(self.output_dir, f"clip_{i}_karaoke.ass")
            self.generate_karaoke_subtitles(clip_words, ass_file)
            
            # Renderizar con Smart Crop y B-Rolls
            safe_title = "".join(c for c in clip['title'] if c.isalnum() or c in (' ', '-', '_'))[:30]
            output_file = os.path.join(self.output_dir, f"VIRAL_{i}_{safe_title}.mp4")
            
            self.process_video_with_smart_crop(
                video_path, start, end, ass_file, output_file,
                face_center_x, source_width, broll_data
            )
            
            clip_duration = time.time() - clip_start_time
            logger.info(f"✅ Clip {i+1}/{total_clips} generado en {clip_duration:.1f}s.")
            
            return {
                "path": output_file,
                "metadata": clip,
                "duration": end - start,
                "word_count": len(clip_words),
                "words": clip_words
            }

        # Ejecutar renders secuencialmente o con concurrencia segura
        import concurrent.futures
        # FASE 3: QA Fix - Limitar workers a 1. Lanzar múltiples instancias de FFmpeg
        # codificando h264 compite destructivamente por la CPU y puede causar deadlocks.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            # Mantener orden original asociando la tarea con su índice
            future_to_idx = {executor.submit(render_clip_task, i, clip): i for i, clip in enumerate(valid_candidates)}
            
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                completed_count += 1
                try:
                    res = future.result()
                    if res:
                        results.append(res)
                    
                    # Progreso basado en clips terminados (exitosos o no)
                    progress_step = 70 + int((completed_count / total_clips) * 25)
                    report(f"Completado clip {completed_count} de {total_clips}", progress_step)
                except Exception as exc:
                    logger.error(f"[ERROR] fatal en tarea de renderizado (clip {idx+1}): {exc}")

            # Reportar progreso final de esta fase
            report("Renderizado de clips finalizado", 95)
        
        report("¡Proceso completado!", 100)

        logger.info(f"\n[INFO] Pipeline completado: {len(results)} clips generados")
        return results


# --- USO DE EJEMPLO ---
if __name__ == "__main__":
    import argparse
    
    # FIX: Forzar UTF-8 en Windows para evitar UnicodeEncodeError con emojis
    if sys.platform == 'win32':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass
    
    parser = argparse.ArgumentParser(description="Viral Video Engine 2026 - Generador Autónomo")
    parser.add_argument("--url", help="URL de YouTube a procesar")
    parser.add_argument("--clips", type=int, default=None, help="Número máximo de clips a generar")
    
    args = parser.parse_args()
    
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        logger.error("No se encontró GEMINI_API_KEY en las variables de entorno.")
        sys.exit(1)
    
    engine = ViralEngine(API_KEY)
    
    target_url = args.url
    if not target_url:
        target_url = input("Introduce URL de YouTube: ")
    
    clips = engine.run_pipeline(target_url)
    
    print(f"\nProceso completado! Se generaron {len(clips)} clips virales.")
    for i, clip in enumerate(clips):
        print(f"   [{i+1}] {clip['metadata']['title']} - {clip['path']}")
