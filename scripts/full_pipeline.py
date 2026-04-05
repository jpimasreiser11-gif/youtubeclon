import os
import subprocess
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv
import glob
from moviepy import *
import sys
import shutil
from pathlib import Path

# Add scripts directory to path to import progress_tracker
script_dir = os.path.dirname(__file__)
project_root = os.path.dirname(script_dir)
sys.path.append(script_dir)
from progress_tracker import JobProgressTracker

# Fix Windows console encoding for Spanish/emoji output
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Load environment variables
env_path = os.path.join(project_root, 'app', '.env')
if not os.path.exists(env_path):
    env_path = os.path.join(project_root, '.env')
load_dotenv(env_path)

from virality_scorer import calculate_virality_score

# Add ffmpeg to PATH
ffmpeg_dir = os.path.abspath(os.path.join(project_root, 'data'))
if ffmpeg_dir not in os.environ.get("PATH", ""):
    os.environ["PATH"] += os.pathsep + ffmpeg_dir
    print(f"Added to PATH: {ffmpeg_dir}")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

import argparse

# Configuration
parser = argparse.ArgumentParser()
parser.add_argument('--video_id', type=str, required=True, help="YouTube Video ID")
parser.add_argument('--project_id', type=str, required=True, help="Database Project ID")
parser.add_argument('--group-topics', action='store_true')
args, unknown = parser.parse_known_args()

VIDEO_ID = args.video_id
PROJECT_ID = args.project_id
DATA_DIR = "data"
OUTPUT_DIR = "output"
CLIPPER_SCRIPT = os.path.join(script_dir, "clipper.py")
REFINE_SCRIPT = os.path.join(script_dir, "refine_segments.py")
SEMANTIC_CHUNKER_SCRIPT = os.path.join(script_dir, "semantic_chunker.py")

# Tools Paths
PYTHON_PATH = sys.executable

# Fallback tools (try to find in Path, otherwise assume commands)
def find_tool(name):
    path = shutil.which(name)
    return path if path else name

WHISPER_PATH = find_tool("whisper")
YTDLP_PATH = find_tool("yt-dlp")

FFMPEG_PATH = os.path.join(project_root, "data", "ffmpeg.exe")
if not os.path.exists(FFMPEG_PATH):
    FFMPEG_PATH = find_tool("ffmpeg")

def get_semantic_chunks(words, video_id):
    """Call the semantic chunker to group words into sentences"""
    print("🧠 Chunking transcript into semantic sentences...")
    input_file = f"{DATA_DIR}/{video_id}_words.json"
    output_file = f"{DATA_DIR}/{video_id}_sentences.json"
    
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(words, f)
        
    cmd = [
        PYTHON_PATH, SEMANTIC_CHUNKER_SCRIPT,
        '--words', input_file,
        '--output', output_file,
        '--group-topics'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('sentences', [])
    except Exception as e:
        print(f"⚠️ Semantic chunking failed: {e}")
        return []

def download_video(video_id):
    print(f"Downloading video {video_id}...")
    url = f"https://www.youtube.com/watch?v={video_id}"
    output_template = f"{DATA_DIR}/{video_id}.%(ext)s"
    
    # Download video + audio merged to mp4
    cmd = [
        YTDLP_PATH, 
        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]', 
        '--merge-output-format', 'mp4',
        '--ffmpeg-location', FFMPEG_PATH, 
        '--output', output_template, 
        url
    ]
    print(f"Running command: {cmd}")
    subprocess.run(cmd, check=True)
    return f"{DATA_DIR}/{video_id}.mp4"

def extract_audio(input_file, video_id):
    print(f"Extracting audio from {input_file}...")
    output_file = f"{DATA_DIR}/{video_id}.mp3"
    
    # Use ffmpeg directly since we have it
    cmd = [FFMPEG_PATH, '-y', '-i', input_file, '-vn', output_file]
    print(f"Running command: {cmd}")
    subprocess.run(cmd, check=True)
    return output_file

def transcribe_audio(video_id, audio_path):
    print("Transcribing with Stable-TS (High Fidelity)...")
    import stable_whisper
    
    model = stable_whisper.load_model('base')
    # regroup=True stabilizes timestamps against silence hallucinations
    result = model.transcribe(audio_path, language='es', regroup=True)
    
    # Save raw result
    transcript_path = f"{DATA_DIR}/{video_id}.json"
    result.save_as_json(transcript_path)
    
    print(f"✅ Transcript saved to: {transcript_path}")
    
    # Extract words structure for pipeline
    # stable-ts result is an object, convert to dict/list
    data = result.to_dict()
    
    # Extract flat word list for other tools
    words = []
    for segment in data.get('segments', []):
        words.extend(segment.get('words', []))
        
    return {
        'text': data['text'],
        'segments': data.get('segments', []),
        'words': words
    }

def extract_words_from_segments(segments):
    """Extract word-level timestamps from Whisper segments"""
    words = []
    for segment in segments:
        # Whisper 'segments' contain word-level data
        if 'words' in segment:
            words.extend(segment['words'])
        else:
            # Fallback: treat entire segment as one "word"
            words.append({
                'word': segment.get('text', '').strip(),
                'start': segment.get('start', 0),
                'end': segment.get('end', 0)
            })
    return words

def detect_silences(audio_path, video_id):
    """Run silence detection script"""
    print("Detecting silences...")
    silence_output = f"{DATA_DIR}/{video_id}_silences.json"
    
    detect_script = os.path.join(os.path.dirname(__file__), 'detect_silences.py')
    
    cmd = [
        PYTHON_PATH, detect_script,
        '--audio', audio_path,
        '--output', silence_output,
        '--min-silence', '400',
        '--threshold', '-38'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Silence detection failed: {e}")
        print("Continuing without silence data...")
        return {'boundary_points': []}
    
    if os.path.exists(silence_output):
        with open(silence_output, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {'boundary_points': []}

def calculate_clip_score_and_tier(clips_data, transcript_sentences):
    """
    Motor de Torneo: Calcula el score absoluto combinando IA + Matemáticas,
    y luego compara todos los clips para asignar una nota final y un Tier.
    """
    if not clips_data:
        return []

    processed_clips = []
    
    # FASE 1: Calificación Absoluta Individual
    for clip in clips_data:
        metrics = clip.get('virality_metrics', {})
        
        # 1. Base AI Score (Promedio de las 4 métricas x 10)
        # Si la IA falló al dar métricas, asignamos 70 por defecto
        if metrics and isinstance(metrics, dict):
            hook = metrics.get('hook_power', 7)
            emotion = metrics.get('emotional_impact', 7)
            value = metrics.get('value_density', 7)
            trend = metrics.get('trend_potential', 7)
            base_score = ((hook + emotion + value + trend) / 40.0) * 100
        else:
            base_score = 75.0

        # 2. Análisis Algorítmico (WPM y Pacing)
        start_id = clip.get('start_id', 0)
        end_id = clip.get('end_id', 0)
        
        # Extraer texto y duración real
        clip_sentences = [s for s in transcript_sentences if start_id <= s['id'] <= end_id]
        if not clip_sentences:
            if 'score' not in clip:
                clip['score'] = int(base_score)
            processed_clips.append(clip)
            continue
            
        start_time = clip_sentences[0]['start']
        end_time = clip_sentences[-1]['end']
        duration = end_time - start_time
        
        text = " ".join([s['text'] for s in clip_sentences])
        word_count = len(text.split())
        
        wpm = (word_count / duration) * 60 if duration > 0 else 0
        clip['wpm'] = wpm
        
        # Modificador matemático de ritmo
        pacing_bonus = 0
        if 140 <= wpm <= 175:
            pacing_bonus = 15  # Ritmo TikTok Perfecto (Rápido y dinámico)
        elif 120 <= wpm < 140 or 175 < wpm <= 190:
            pacing_bonus = 5   # Ritmo Aceptable
        else:
            pacing_bonus = -10 # Demasiado lento o incomprensiblemente rápido

        # 3. Modificador de Gancho (Hooks cortos = mejor retención)
        hook_text = clip.get('hook', '')
        hook_bonus = 5 if len(hook_text.split()) <= 12 else 0

        # Suma total bruta
        raw_score = base_score + pacing_bonus + hook_bonus
        clip['raw_score'] = min(max(raw_score, 10), 99) # Nunca pasamos de 99 aquí
        
        clip['start_time'] = start_time
        clip['end_time'] = end_time
        
        processed_clips.append(clip)

    # FASE 2: Torneo y Normalización Relativa
    # Ordenamos del mejor al peor
    processed_clips.sort(key=lambda x: x.get('raw_score', 0), reverse=True)
    
    if processed_clips:
        best_raw_score = processed_clips[0].get('raw_score', 0)
        
        for i, clip in enumerate(processed_clips):
            if 'raw_score' not in clip:
                clip['virality_score'] = clip.get('score', 70)
                clip['tier'] = "C"
                continue
                
            # Normalizamos respecto al mejor clip del video
            # Esto asegura que el mejor clip siempre roce el 95-99
            if best_raw_score > 0:
                normalized = (clip['raw_score'] / best_raw_score) * 96
            else:
                normalized = clip['raw_score']
            
            # Bonus de Pódium
            if i == 0:
                normalized += 3 # El #1 siempre es el Rey (Llega a 99)
            elif i == 1:
                normalized += 1 # El #2 es sólido
                
            final_score = int(min(normalized, 99))
            clip['score'] = final_score
            clip['virality_score'] = final_score
            
            # Asignación de Tier
            if final_score >= 90:
                clip['tier'] = "S" # God Tier
            elif final_score >= 80:
                clip['tier'] = "A" # Viral
            elif final_score >= 70:
                clip['tier'] = "B" # Decente
            else:
                clip['tier'] = "C" # Relleno
                
            # Limpiamos variables temporales
            clip.pop('raw_score', None)

    return processed_clips

def analyze_transcript(transcript_data, silence_data, video_id):
    """
    Logic-First Analysis:
    1. Chunk words into Semantic Sentences (Spacy)
    2. Prompt Gemini to select SENTENCE RANGES (ID-based)
    3. Map IDs back to precise stable-ts timestamps
    """
    print("Analyzing with Gemini (Semantic Sentence Logic)...")
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    words = transcript_data.get('words', [])
    
    # 1. Get Semantic Chunks
    sentences = get_semantic_chunks(words, video_id)
    if not sentences:
        print("⚠️ Semantic chunking failed, falling back to raw text...")
        # Fallback to old method if chunking fails
        # (Simplified fallback omitted for brevity, assuming chunking works)
        return []

    # 2. Build Context with IDs
    transcript_block = ""
    current_topic = None
    for s in sentences:
        if s.get('topic') and s['topic'] != current_topic:
            current_topic = s['topic']
            transcript_block += f"\n--- TOPIC: {current_topic} ---\n"
        transcript_block += f"[{s['id']}] {s['text']}\n"
        
    print(f"📊 Prepared {len(sentences)} semantic sentences for memory context.")

    prompt = f"""
ACT AS: Expert Viral Video Editor.
TASK: Identify 3 HIGH-POTENTIAL viral clips from this transcript.

TRANSCRIPT (Sentences with IDs):
{transcript_block}

CRITERIA:
1. **Unidad Lógica (PRIORIDAD ABSOLUTA)**: El clip debe ser una historia o pensamiento COMPLETO. Debe contener la PREMISA (el gancho inicial), el DESARROLLO (la explicación detallada), y la CONCLUSIÓN (el cierre natural).
2. **Prohibido cortar explicaciones largas**: Si el creador está contando una anécdota, dando una lista de consejos o desarrollando una idea, no la cortes por la mitad SOLO PARA CUMPLIR EL TIEMPO. Incluye toda la explicación lógica.
3. **REGLA DE DURACIÓN**: Lo ideal es que los clips duren entre 30 segundos y 3 minutos, pero NUNCA sacrifiques la regla #1 (Lógica). Selecciona el rango de IDs que cubra la idea por completo, incluso si tienes que pasarte algunos segundos de los 3 minutos.
4. **Sentido por sí solo**: Si el espectador ve este clip sin conocer el resto del video, debe entenderlo perfectamente al 100%. No incluyas frases que dependan de contexto anterior.

INSTRUCTIONS:
- Select a range of Sentence IDs (e.g., Start: 12, End: 65).
- DO NOT invent timestamps. Use ONLY IDs.

RETURN JSON EXACTLY IN THIS FORMAT (No markdown, just JSON list):
[
  {{
    "title": "Viral Title Here",
    "start_id": 10,
    "end_id": 65,
    "hook": "The exact opening hook sentence",
    "visual_keywords": ["money", "crypto"],
    "virality_metrics": {{
      "hook_power": 9, 
      "emotional_impact": 8,
      "value_density": 9,
      "trend_potential": 8
    }}
  }}
]
    """
    
    import time
    max_retries = 5
    base_delay = 15
    
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            text = response.text
            
            # FASE 2 - QA Fix: Extraer JSON aislando de markdown extra de la respuesta de Gemini y manejando errores sin crashear el for.
            import json
            
            json_match = re.search(r'(\[.*\])', text, re.DOTALL)
            try:
                if json_match:
                    raw_clips = json.loads(json_match.group(1))
                else:
                    raw_clips = json.loads(text)
            except json.JSONDecodeError as je:
                print(f"⚠️  JSON Malformado en intento {attempt + 1}: {je}")
                if attempt < max_retries - 1:
                    continue # Reintentar prompt
                break # Máximos intentos

                final_clips = []
                
                # 3. Map IDs to Timestamps
                for rc in raw_clips:
                    try:
                        s_id = rc.get('start_id')
                        e_id = rc.get('end_id')
                        
                        if s_id is None or e_id is None:
                            continue
                            
                        # Find sentences (1-based ID -> 0-based index?)
                        # Assuming IDs are sequential 1..N matches list index 0..N-1
                        start_sent = next((s for s in sentences if s['id'] == s_id), None)
                        end_sent = next((s for s in sentences if s['id'] == e_id), None)
                        
                        if start_sent and end_sent:
                            clip = {
                                "title": rc['title'],
                                "hook": rc.get('hook', ''),
                                "virality_metrics": rc.get('virality_metrics', {}),
                                "start_id": s_id,
                                "end_id": e_id
                            }
                            final_clips.append(clip)
                            print(f"  ✅ Clip '{clip['title']}': Sentences {s_id}-{e_id} ({clip['start_time']:.1f}s - {clip['end_time']:.1f}s)")
                    except Exception as e:
                        print(f"  ⚠️ Error parsing clip {rc}: {e}")
                
                return final_clips
            return []
                
                
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Gemini Analysis API Error intento {attempt + 1}: {error_msg}")
            if "429" in error_msg or "quota" in error_msg.lower():
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    print(f"   ⏳ Rate limit. Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                    continue
            break

    # FASE 2 - QA Fix: Si fallan todos los reintentos, retornamos lista vacía para que el validador final lance error de "0 clips" 
    # de manera limpia y no siga renderizando un clip falso
    return []

def verify_clip_coherence(clip_text):
    """Phase 2: Use Gemini to audit if a clip is logically complete"""
    print(f"🧐 Auditing clip coherence...")
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    prompt = f"""
    ANALIZA ESTE FRAGMENTO DE VIDEO:
    "{clip_text}"
    
    ¿El hablante termina de explicar su idea o el pensamiento se corta abruptamente?
    Responde ÚNICAMENTE en este formato JSON:
    {{
      "status": "COMPLETO" o "INCOMPLETO",
      "reason": "breve explicación",
      "action": "KEEP" o "EXTEND_END" o "EXTEND_START"
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        print(f"⚠️ Coherence audit failed: {e}")
    
    return {"status": "COMPLETO", "action": "KEEP"}

def run_clipper(video_id, clips, words=None, video_path=None):
    print("Running clipper...")
    input_data = {
        'id': video_id, 
        'clips': clips,
        'words': words if words else [],
        'video_path': video_path
    }
    # Save to temp file to avoid Windows CMD length limit (32K chars)
    input_file = f"{DATA_DIR}/{video_id}_clipper_input.json"
    with open(input_file, 'w', encoding='utf-8') as f:
        json.dump(input_data, f, ensure_ascii=False)
    print(f"📄 Clipper input saved to: {input_file}")
    subprocess.run([PYTHON_PATH, CLIPPER_SCRIPT, input_file], check=True)

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    print(f"Processing Video ID: {VIDEO_ID}")
    
    # Initialize Progress Tracker
    tracker = JobProgressTracker(PROJECT_ID)
    tracker.update("downloading", 0.0, "Iniciando descarga...")
    
    # 1. Download Video (Ensure we have it)
    input_video = download_video(VIDEO_ID)
    tracker.update("downloading", 1.0, "Descarga completada")
    print(f"Using video: {input_video}")
    
    # 2. Extract Audio
    tracker.update("audio_prep", 0.0, "Extrayendo audio...")
    raw_audio = extract_audio(input_video, VIDEO_ID)
    
    # 3. Restore Audio (Professional Grade)
    print("\n🎧 Phase 7: Professional Audio Restoration...")
    tracker.update("audio_prep", 0.5, "Restaurando audio (IA)...")
    restored_audio = f"{DATA_DIR}/{VIDEO_ID}_restored.mp3"
    restore_script = os.path.join(os.path.dirname(__file__), 'audio_processor.py')
    
    try:
        subprocess.run([PYTHON_PATH, restore_script, '--input', raw_audio, '--output', restored_audio], check=True)
        print(f"✅ Audio restored and normalized: {restored_audio}")
        
        # Merge restored audio back into a master video for quality consistency
        master_video = f"{DATA_DIR}/{VIDEO_ID}_master.mp4"
        print("🎬 Merging restored audio into master video...")
        merge_cmd = [
            FFMPEG_PATH, "-y",
            "-i", input_video,
            "-i", restored_audio,
            "-map", "0:v",
            "-map", "1:a",
            "-c:v", "copy",
            "-c:a", "aac",
            master_video
        ]
        subprocess.run(merge_cmd, check=True)
        active_video = master_video
        active_audio = restored_audio
    except Exception as e:
        print(f"⚠️ Audio restoration phase failed: {e}. Falling back to default.")
        active_video = input_video
        active_audio = raw_audio
    
    tracker.update("audio_prep", 1.0, "Audio listo")

    # 4. Transcribe
    tracker.update("transcribing", 0.0, "Transcribiendo con Stable-TS...")
    transcript_data = transcribe_audio(VIDEO_ID, active_audio)
    tracker.update("transcribing", 1.0, "Transcripción completada")
    print(f"Transcript: {len(transcript_data['text'])} chars, {len(transcript_data.get('words', []))} words")
    
    # 5. Detect Silences
    tracker.update("analyzing", 0.0, "Detectando silencios y pausas...")
    silence_data = detect_silences(active_audio, VIDEO_ID)
    boundary_count = len(silence_data.get('boundary_points', []))
    print(f"Found {boundary_count} silence boundary points")
    
    # 6. Analyze with Gemini
    tracker.update("analyzing", 0.5, "Gemini analizando potencial viral...")
    raw_clips = analyze_transcript(transcript_data, silence_data, VIDEO_ID)
    print(f"Gemini suggested {len(raw_clips)} clips")
    
    # REGLAS DE TIEMPO ESTRICTAS (Mínimo 1 min, Máximo 3 min)
    MIN_CLIP_DURATION = 30.0
    MAX_CLIP_DURATION = 180.0 
    STOP_WORDS_END = ["y bueno", "entonces", "pero como", "o sea", "ehhh", "entonces nada", "pues nada", "y nada"]

    # 6.5 Phase 2: Two-Pass Verification & Coherence Audit
    audited_clips = []
    if raw_clips:
        tracker.update("analyzing", 0.9, "Auditoría de coherencia lógica...")
        print("\n🔍 Phase 2: Auditing clip coherence & Pacing...")
        sentences = get_semantic_chunks(transcript_data.get('words', []), VIDEO_ID)
        
        for rc in raw_clips:
            # Check for fallback clip (missing IDs)
            s_id = rc.get('start_id')
            e_id = rc.get('end_id')
            if s_id is None or e_id is None:
                audited_clips.append(rc)
                continue

            # 1. Calc Duration
            duration = rc['end_time'] - rc['start_time']
            
            # 2. Reconstruct text
            clip_sentences = [s['text'] for s in sentences if s_id <= s['id'] <= e_id]
            clip_text = " ".join(clip_sentences)
            
            # 3. Coherence Audit & Duration Check
            audit = verify_clip_coherence(clip_text)
            
            # Si está incompleto, o si dura menos de 1 minuto, INTENTAMOS EXTENDERLO
            if (audit['status'] == "INCOMPLETO" or duration < MIN_CLIP_DURATION) and duration < MAX_CLIP_DURATION:
                if duration < MIN_CLIP_DURATION:
                    print(f"  ⚠️ Clip '{rc['title']}' es muy corto ({duration:.1f}s). Extendiendo para llegar al minuto...")
                else:
                    print(f"  ❌ Clip '{rc['title']}' está INCOMPLETO lógicamente. Añadiendo contexto...")
                
                # Intentamos añadir hasta 8 oraciones para cerrar bien la idea (ya que tenemos hasta 3 minutos de margen)
                for _ in range(8): 
                    if audit['action'] == "EXTEND_END" or duration < MIN_CLIP_DURATION:
                        rc['end_id'] += 1
                    elif audit['action'] == "EXTEND_START":
                        rc['start_id'] = max(1, rc['start_id'] - 1)
                    
                    # Update timestamps
                    start_sent = next((s for s in sentences if s['id'] == rc['start_id']), None)
                    end_sent = next((s for s in sentences if s['id'] == rc['end_id']), None)
                    if start_sent and end_sent:
                        new_duration = end_sent['end'] - start_sent['start']
                        if new_duration > MAX_CLIP_DURATION + 10:
                            print(f"  ⚠️ Extensión abortada: superaría el límite máximo de 3 minutos ({MAX_CLIP_DURATION}s).")
                            break
                        
                        rc['start_time'] = start_sent['start']
                        rc['end_time'] = end_sent['end']
                        duration = new_duration
                        clip_text = " ".join([s['text'] for s in sentences if rc['start_id'] <= s['id'] <= rc['end_id']])
                        
                        # Re-audit rápido si ya pasamos el minuto
                        if duration >= MIN_CLIP_DURATION:
                            audit = verify_clip_coherence(clip_text)
                            if audit['status'] == "COMPLETO":
                                print(f"  ✅ Lógica completada y duración correcta. Final: {duration:.1f}s")
                                break
            
            # 4. Filter Stop-Words at the end
            last_words = clip_text.lower().split()[-4:] # Last 4 words
            last_phrase = " ".join(last_words)
            for sw in STOP_WORDS_END:
                if sw in last_phrase:
                    print(f"  ✂️ Stop-word '{sw}' detected at end, flagging for Phase 4 trim.")
                    rc['has_stopword'] = True
                    break

            # 5. Pacing Analysis (WPM)
            word_count = len(clip_text.split())
            wpm = (word_count / duration) * 60 if duration > 0 else 0
            rc['wpm'] = round(wpm, 1)

            audited_clips.append(rc)
        raw_clips = audited_clips
    
    # 7. Refine clip boundaries
    if raw_clips:
        tracker.update("refining", 0.0, "Refinando bordes de clips...")
        print("\n🔧 Refining clip boundaries...")
        raw_clips_file = f"{DATA_DIR}/{VIDEO_ID}_raw_clips.json"
        with open(raw_clips_file, 'w', encoding='utf-8') as f:
            json.dump(raw_clips, f, indent=2)
            
        words_file = f"{DATA_DIR}/{VIDEO_ID}.json"
        silences_file = f"{DATA_DIR}/{VIDEO_ID}_silences.json"
        refined_file = f"{DATA_DIR}/{VIDEO_ID}_clips_refined.json"
        
        cmd = [
            PYTHON_PATH, REFINE_SCRIPT,
            '--clips', raw_clips_file,
            '--words', words_file,
            '--video', input_video,
            '--silences', silences_file,
            '--output', refined_file
        ]
        
        try:
            print(f"Running: {' '.join(cmd)}")
            subprocess.run(cmd, check=True)
            with open(refined_file, 'r', encoding='utf-8') as f:
                refined_data = json.load(f)
                clips = refined_data.get('clips', raw_clips)
            print(f"✅ Using {len(clips)} refined clips")
        except Exception as e:
            print(f"⚠️ Boundary refinement failed: {e}")
            clips = raw_clips
    else:
        clips = raw_clips
    
    # 8. Generate Clips (Aduana Final de Longitud)
    if clips:
        # 8.1 Calcular Puntajes de Viralidad y Tiers (MOTOR DE TORNEO)
        scored_clips = calculate_clip_score_and_tier(clips, sentences)
        
        valid_clips = []
        for c in scored_clips:
            duration = c.get('end_time', 0) - c.get('start_time', 0)
            
            # Priorizamos lógica: damos hasta MAX + 60 segundos de margen arriba
            if MIN_CLIP_DURATION - 10.0 <= duration <= MAX_CLIP_DURATION + 60.0:
                print(f"✅ Clip '{c.get('title')}' aceptado: {duration:.1f}s | Score: {c.get('virality_score', c.get('score', 0))} (Tier {c.get('tier', 'N/A')}) | WPM: {c.get('wpm', 0):.0f}")
                valid_clips.append(c)
            else:
                print(f"⚠️ Clip descartado por duración extrema: '{c.get('title')}' (Duró {duration:.2f}s)")
                
        if not valid_clips:
            print("❌ No valid clips remaining after validation.")
            return

        if valid_clips:
            tracker.update("rendering", 0.0, "Iniciando renderizado final...")
            run_clipper(VIDEO_ID, valid_clips, transcript_data.get('words', []), video_path=active_video)
            
            # [NEW] Enterprise Post-Processing (Pilar 2)
            for i, clip in enumerate(valid_clips):
                clip_path = f"output/{VIDEO_ID}_clip_{i}.mp4"
                if not os.path.exists(clip_path): continue
                
                # 1. Smart Reframing (Face Tracking)
                if "--smart-reframe" in sys.argv:
                    print(f"🪄 [Enterprise] Applying Dynamic Face Tracking to clip {i}...")
                    temp_crop = f"output/{VIDEO_ID}_clip_{i}_cropped.mp4"
                    crop_cmd = [PYTHON_PATH, "scripts/smart_crop.py", "--input", clip_path, "--output", temp_crop]
                    try:
                        subprocess.run(crop_cmd, check=True)
                        os.replace(temp_crop, clip_path)
                    except Exception as e:
                        print(f"❌ Smart Reframing failed for clip {i}: {e}")
                
                # 2. B-Roll Injection
                if "--b-roll" in sys.argv and clip.get("visual_keywords"):
                    print(f"🎬 [Enterprise] Injecting B-Roll to clip {i} (Keywords: {clip['visual_keywords']})...")
                    temp_broll = f"output/{VIDEO_ID}_clip_{i}_broll.mp4"
                    kw_json = json.dumps(clip["visual_keywords"])
                    broll_cmd = [PYTHON_PATH, "scripts/broll_injector.py", "--video", clip_path, "--keywords", kw_json, "--output", temp_broll]
                    try:
                        subprocess.run(broll_cmd, check=True)
                        os.replace(temp_broll, clip_path)
                    except Exception as e:
                        print(f"❌ B-Roll Injection failed for clip {i}: {e}")

            print("\n✅ Enterprise Pipeline execution complete!")
            tracker.update("rendering", 1.0, "Proceso completado")
            print(f"📁 Check output/ folder for rendered clips with AI Polish")
        else:
            print("❌ No clips identified.")

if __name__ == "__main__":
    main()
