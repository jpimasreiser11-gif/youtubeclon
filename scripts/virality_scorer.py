import math

VIRAL_HOOK_KEYWORDS = [
    "secret", "never", "stop", "amazing", "how to", "why you", "most", 
    "biggest", "mistake", "hack", "trick", "finally", "truth", "discovered",
    "hidden", "warning", "don't", "must", "important", "new"
]

def calculate_virality_score(words, duration):
    """
    Calculates a virality score from 0 to 100 based on transcript analysis.
    
    Stats: 
    - Hook Strength (40%)
    - Pace/Energy (30%)
    - Content Value (30%)
    """
    if not words or duration <= 0:
        return 0
        
    score = 0
    
    # 1. Hook Strength (First 3-5 seconds)
    hook_score = 0
    hook_duration = min(duration, 5.0)
    hook_words = [w['word'].lower() for w in words if w.get('start', 0) <= hook_duration]
    
    found_hook_keywords = 0
    for kw in VIRAL_HOOK_KEYWORDS:
        if any(kw in hw for hw in hook_words):
            found_hook_keywords += 1
            
    # Exponential-ish scaling for keywords
    hook_score = min(40, found_hook_keywords * 15) 
    # Bonus for question mark at start or exclamation (if available in raw text)
    # Since we have word list, we check for specific 'hook' patterns
    score += hook_score
    
    # 2. Pace (Words Per Second)
    # Ideal for short form: 2.5 to 4.0 words/sec
    wps = len(words) / duration
    pace_score = 0
    if 2.5 <= wps <= 4.0:
        pace_score = 30
    elif 2.0 <= wps < 2.5 or 4.0 < wps <= 5.0:
        pace_score = 20
    elif 1.5 <= wps < 2.0:
        pace_score = 10
    else:
        pace_score = 5
    score += pace_score
    
    # 3. Content Value / Sentiment (Keyword density for value)
    # Simplified sentiment/value check
    value_keywords = ["learn", "improve", "better", "best", "fast", "simple", "easy", "life", "money", "future"]
    found_value = 0
    for w in words:
        if any(vk in w['word'].lower() for vk in value_keywords):
            found_value += 1
            
    density = found_value / len(words) if words else 0
    value_score = min(30, density * 300) # Density of 10% is maxed
    score += value_score
    
    return min(100, round(score))

def get_virality_label(score):
    if score >= 80: return "VERY HIGH (Viral Potential)"
    if score >= 60: return "HIGH"
    if score >= 40: return "MODERATE"
    return "LOW"

if __name__ == "__main__":
    # Test
    test_words = [
        {"word": "The", "start": 0.1, "end": 0.3},
        {"word": "secret", "start": 0.4, "end": 0.8},
        {"word": "to", "start": 0.9, "end": 1.1},
        {"word": "making", "start": 1.2, "end": 1.5},
        {"word": "money", "start": 1.6, "end": 2.0}
    ]
    s = calculate_virality_score(test_words, 2.0)
    print(f"Test Score: {s} - {get_virality_label(s)}")
