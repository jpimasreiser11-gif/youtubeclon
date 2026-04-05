"""
Clip Post-Processor: Corrección Inteligente de Finales de Clips
Ajusta end_time para que los clips terminen en momentos naturales,
no a mitad de frase o antes del payoff completo.
"""

import json
from typing import List, Dict, Any, Optional

class Word:
    """Represents a word with timing information"""
    def __init__(self, text: str, start: float, end: float):
        self.text = text
        self.start = start
        self.end = end

class Silence:
    """Represents a silence period"""
    def __init__(self, start: float, duration: float):
        self.start = start
        self.duration = duration

def detect_silences(words: List[Word], min_gap: float = 0.5) -> List[Silence]:
    """
    Detecta silencios entre palabras
    
    Args:
        words: Lista de palabras con timestamps
        min_gap: Duración mínima en segundos para considerar un silencio
    
    Returns:
        Lista de silencios detectados
    """
    silences = []
    
    for i in range(len(words) - 1):
        gap = words[i + 1].start - words[i].end
        if gap >= min_gap:
            silences.append(Silence(words[i].end, gap))
    
    return silences

def has_strong_punctuation(text: str) -> bool:
    """Verifica si el texto termina con puntuación fuerte"""
    return text.rstrip()[-1] in ['.', '!', '?', '…'] if text.strip() else False

def find_next_silence(current_time: float, silences: List[Silence], min_duration: float = 0.5) -> Optional[float]:
    """
    Encuentra el siguiente silencio significativo después de current_time
    
    Args:
        current_time: Tiempo actual en segundos
        silences: Lista de silencios detectados
        min_duration: Duración mínima del silencio
    
    Returns:
        Timestamp del inicio del siguiente silencio, o None
    """
    for silence in silences:
        if silence.start > current_time and silence.duration >= min_duration:
            return silence.start
    return None

def extract_keywords(description: str) -> List[str]:
    """
    Extrae palabras clave importantes de una descripción
    Simplificado: toma las palabras más largas
    """
    words = description.lower().split()
    # Filtrar palabras comunes y cortas
    stopwords = {'el', 'la', 'los', 'las', 'un', 'una', 'de', 'que', 'en', 'y', 'a', 'con', 'por', 'para'}
    keywords = [w for w in words if len(w) > 4 and w not in stopwords]
    return keywords[:5]  # Top 5 keywords

def keywords_in_range(keywords: List[str], start_time: float, end_time: float, words: List[Word]) -> bool:
    """
    Verifica si las keywords aparecen en el rango de tiempo especificado
    """
    words_in_range = [w.text.lower() for w in words if start_time <= w.start <= end_time]
    text_in_range = ' '.join(words_in_range)
    
    # Al menos 2 de las keywords deben aparecer
    matches = sum(1 for kw in keywords if kw in text_in_range)
    return matches >= min(2, len(keywords))

def find_payoff_end(payoff_keywords: List[str], words: List[Word], after_time: float) -> float:
    """
    Encuentra el final del payoff buscando la última keyword
    """
    max_end = after_time
    
    for word in words:
        if word.start < after_time:
            continue
        if any(kw in word.text.lower() for kw in payoff_keywords):
            max_end = word.end
    
    return max_end

def fix_clip_ending(clip: Dict[str, Any], words: List[Word], silences: List[Silence], visual_cuts: List[float] = []) -> Dict[str, Any]:
    """
    Ajusta el end_time de un clip para terminar en un momento natural
    [ENTERPRISE UPGRADE]: Adds visual snapping, dynamic padding, and stop-word trimming.
    """
    original_start = clip['start_time']
    original_end = clip['end_time']
    adjusted_start = original_start
    adjusted_end = original_end
    auto_adjusted = False
    
    # 1. Base Logic: Punctuation & Silences
    relevant_words = [w for w in words if w.start <= original_end + 10]
    last_word = max([w for w in relevant_words if w.end <= original_end], key=lambda w: w.end, default=None)
    
    if last_word and not has_strong_punctuation(last_word.text):
        next_silence = find_next_silence(original_end, silences, min_duration=0.5)
        if next_silence and next_silence <= original_end + 5.0:
            adjusted_end = next_silence
            auto_adjusted = True

    # 2. [NEW] Phase 5: Scene Cut Snap (within 0.4s)
    if visual_cuts:
        nearest_cut = min(visual_cuts, key=lambda c: abs(c - adjusted_end))
        if abs(nearest_cut - adjusted_end) < 0.4:
            adjusted_end = nearest_cut
            auto_adjusted = True

    # 3. [NEW] Phase 4: Dynamic Padding (0.15s start / 0.2s end)
    adjusted_start = max(0, adjusted_start - 0.15)
    adjusted_end = adjusted_end + 0.2
    
    # 4. [NEW] Stop-word Trimming (Phase 5)
    STOP_WORDS = {"bueno", "entonces", "nada", "ehhh", "o sea"}
    if last_word and last_word.text.lower().strip(',.') in STOP_WORDS:
        adjusted_end -= 0.6 # Remove the trailing word time
        auto_adjusted = True
    
    # Security: Ensure duration breaker (max 65s)
    if (adjusted_end - adjusted_start) > 65.0:
        adjusted_end = adjusted_start + 60.0
    
    return {
        **clip,
        'start_time': round(adjusted_start, 2),
        'end_time': round(adjusted_end, 2),
        'end_confidence': 80 if auto_adjusted else 100,
        'auto_adjusted': auto_adjusted
    }

def process_all_clips(clips: List[Dict[str, Any]], transcript_words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Procesa todos los clips de un proyecto
    
    Args:
        clips: Lista de clips generados por Gemini
        transcript_words: Lista de palabras del transcript completo
                         [{"text": "hola", "start": 0.5, "end": 0.8}, ...]
    
    Returns:
        Lista de clips con end_time ajustados
    """
    # Convertir transcript a objetos Word
    words = [Word(w['text'], w['start'], w['end']) for w in transcript_words]
    
    # Detectar silencios
    silences = detect_silences(words)
    
    print(f"📊 Detectados {len(silences)} silencios naturales")
    
    # Procesar cada clip
    fixed_clips = []
    for i, clip in enumerate(clips):
        fixed_clip = fix_clip_ending(clip, words, silences)
        
        if fixed_clip['auto_adjusted']:
            original = clip['end_time']
            adjusted = fixed_clip['end_time']
            print(f"✓ Clip {i+1}: ajustado de {original:.1f}s → {adjusted:.1f}s (confianza: {fixed_clip['end_confidence']})")
        
        fixed_clips.append(fixed_clip)
    
    return fixed_clips

# Ejemplo de uso
if __name__ == "__main__":
    # Test
    test_clip = {
        'title': 'Test Clip',
        'start_time': 10.0,
        'end_time': 45.0,
        'payoff_description': 'La conclusión sorprendente del experimento'
    }
    
    test_words = [
        {'text': 'Y', 'start': 43.0, 'end': 43.1},
        {'text': 'por', 'start': 43.2, 'end': 43.4},
        {'text': 'eso', 'start': 43.5, 'end': 43.8},
        {'text': 'la', 'start': 44.0, 'end': 44.1},
        {'text': 'conclusión', 'start': 44.2, 'end': 44.8},
        {'text': 'del', 'start': 44.9, 'end': 45.0},
        {'text': 'experimento', 'start': 45.1, 'end': 45.8},
        {'text': 'fue', 'start': 46.0, 'end': 46.2},
        {'text': 'sorprendente.', 'start': 46.3, 'end': 47.0},
    ]
    
    fixed = process_all_clips([test_clip], test_words)
    print(json.dumps(fixed[0], indent=2))
