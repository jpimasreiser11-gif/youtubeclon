import json
import os

DISFLUENCIES = ["eh", "um", "uh", "ah", "este", "o sea", "bueno", "pero"]

def detect_removals(words, start_time, end_time, min_pause=1.5):
    """
    Identifies segments to remove within a clip:
    1. Filler words (disfluencies)
    2. Long pauses (silences between words)
    """
    removals = []
    
    # Filter words within clip range
    clip_words = [w for w in words if w['start'] >= start_time and w['end'] <= end_time]
    
    if not clip_words:
        return []

    # 1. Detect Filler Words
    for i, word in enumerate(clip_words):
        clean_word = word['word'].lower().strip().replace(".", "").replace(",", "")
        if clean_word in DISFLUENCIES:
            # Mark for removal: [start, end]
            removals.append({
                'start': word['start'],
                'end': word['end'],
                'reason': f"filler: {clean_word}"
            })

    # 2. Detect Long Pauses between words
    for i in range(len(clip_words) - 1):
        current_word_end = clip_words[i]['end']
        next_word_start = clip_words[i+1]['start']
        
        pause_duration = next_word_start - current_word_end
        if pause_duration > min_pause:
            # Mark the middle of the pause for removal to keep some natural air
            # We leave 0.2s at the end of current and 0.2s before next
            remove_start = current_word_end + 0.2
            remove_end = next_word_start - 0.2
            
            if remove_end > remove_start:
                removals.append({
                    'start': remove_start,
                    'end': remove_end,
                    'reason': "long pause"
                })

    # 3. Merge overlapping or adjacent removals
    if not removals:
        return []
        
    removals.sort(key=lambda x: x['start'])
    merged = []
    if removals:
        curr = removals[0]
        for next_rem in removals[1:]:
            if next_rem['start'] <= curr['end'] + 0.1: # 100ms gap merge
                curr['end'] = max(curr['end'], next_rem['end'])
            else:
                merged.append(curr)
                curr = next_rem
        merged.append(curr)
        
    return merged

if __name__ == "__main__":
    # Test logic
    test_words = [
        {"word": "Hola", "start": 1.0, "end": 1.5},
        {"word": "eh", "start": 1.6, "end": 1.9},
        {"word": "mundo", "start": 3.5, "end": 4.0}
    ]
    print(detect_removals(test_words, 0, 10, min_pause=1.0))
