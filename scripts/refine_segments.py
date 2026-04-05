import argparse
import json
import os
import sys
import signal
import threading
from typing import List, Dict, Optional
import numpy as np
from pathlib import Path

# Try to import scenedetect
try:
    from scenedetect import detect, ContentDetector
except ImportError:
    print("⚠️ scenedetect not found, visual cuts will be disabled")
    detect = None

def get_visual_cuts(video_path: str, timeout: int = 60) -> List[float]:
    """Detect scene changes using ContentDetector with timeout"""
    if not detect or not os.path.exists(video_path):
        return []
    
    print(f"🎬 Detecting visual cuts for: {video_path} (timeout: {timeout}s)")
    result = []
    error = [None]
    
    def _detect():
        try:
            scene_list = detect(video_path, ContentDetector())
            result.extend([scene[0].get_seconds() for scene in scene_list])
        except Exception as e:
            error[0] = e
    
    thread = threading.Thread(target=_detect)
    thread.daemon = True
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        print(f"⚠️ Visual cut detection timed out after {timeout}s, skipping (Audio+Text still active)")
        return []
    
    if error[0]:
        print(f"⚠️ Visual cut detection failed: {error[0]}")
        return []
    
    print(f"✅ Found {len(result)} visual cuts")
    return result

def get_text_boundary_score(time: float, words: List[Dict], window: float = 1.0) -> float:
    """
    Check if a time is near a punctuation mark.
    Returns 1.0 for hard punctuation (. ! ?), 0.5 for soft (, ; -), or 0.0
    """
    for word in words:
        # Check words ending near this time
        if abs(word['end'] - time) < window:
            text = word['word'].strip()
            if text.endswith(('.', '!', '?', ':')):
                return 1.0
            if text.endswith((',', ';', '-', '...')):
                return 0.5
    return 0.0

def find_best_boundary(
    target_time: float, 
    words: List[Dict], 
    visual_cuts: List[float], 
    silences: List[float],
    search_range: float = 1.5,
    is_start: bool = True
) -> float:
    """
    Find the optimal boundary by maximizing a weighted score of:
    - Punctuation (Text)
    - Silences (Audio)
    - Scene Cuts (Visual)
    """
    # Create a range of candidates every 50ms
    candidates = np.arange(target_time - search_range, target_time + search_range, 0.05)
    best_time = target_time
    max_score = -1.0
    
    # Weights (Magnetic Logic)
    W_TEXT = 1.0   # Anchor to sentence structure
    W_AUDIO = 0.5  # Snap to silence
    W_VISUAL = 0.5 # Snap to cut
    
    for t in candidates:
        if t < 0: continue
        
        # 1. Text Score (Punctuation)
        text_score = get_text_boundary_score(t, words)
        
        # 2. Audio Score (Near silence)
        audio_score = 0.0
        if silences:
            for s in silences:
                dist_to_start = abs(s['start'] - t)
                dist_to_end = abs(s['end'] - t)
                dist = min(dist_to_start, dist_to_end)
                
                if dist < 0.3:
                    base_score = 0.5 if dist < 0.3 else 0.0
                    if dist < 0.1: base_score = 1.0
                    duration_bonus = 1.0 if s['duration'] > 0.8 else 0.0
                    audio_score = max(audio_score, base_score + duration_bonus)
            
        # 3. Visual Score (Scene Cut)
        visual_score = 0.0
        nearest_cut = min([abs(c - t) for c in visual_cuts]) if visual_cuts else 10.0
        if nearest_cut < 0.1:
            visual_score = 1.0
        elif nearest_cut < 0.3:
            visual_score = 0.5
                
        # 4. Proximity Penalty
        proximity = 1.0 - (abs(t - target_time) / search_range)
        
        # Increase weight of Audio if it's a deep silence
        W_AUDIO_DYNAMIC = W_AUDIO
        if audio_score > 1.0: # Means we found a deep silence
            W_AUDIO_DYNAMIC *= 2.0
            
        # Combine
        total_score = (text_score * W_TEXT + audio_score * W_AUDIO_DYNAMIC + visual_score * W_VISUAL) * proximity
            
        if total_score > max_score:
            max_score = total_score
            best_time = t
            
    # If no real boundary found (score 0), just keep original
    if max_score <= 0.1:
        return target_time
        
    return best_time

def refine_clips(clips, words, video_path, silences):
    visual_cuts = get_visual_cuts(video_path) if video_path else []
    
    # [NEW] Phase 4 & 5 Polish
    refined_clips = []
    print(f"✨ Refining {len(clips)} clips with Enterprise-Grade Polish...")
    
    for clip in clips:
        orig_start = clip['start_time']
        orig_end = clip['end_time']
        
        # 1. Base Boundary Analysis
        new_start = find_best_boundary(orig_start, words, visual_cuts, silences, is_start=True)
        new_end = find_best_boundary(orig_end, words, visual_cuts, silences, is_start=False)
        
        # 2. [NEW] Phase 5: Scene Cut Snap (within 0.4s)
        # If a visual cut is extremely close, prioritize it over audio/text to avoid focal glitches
        if visual_cuts:
            nearest_start_cut = min(visual_cuts, key=lambda c: abs(c - new_start))
            if abs(nearest_start_cut - new_start) < 0.4:
                print(f"  🎬 Snapping START to visual cut at {nearest_start_cut:.2f}s")
                new_start = nearest_start_cut
                
            nearest_end_cut = min(visual_cuts, key=lambda c: abs(c - new_end))
            if abs(nearest_end_cut - new_end) < 0.4:
                print(f"  🎬 Snapping END to visual cut at {nearest_end_cut:.2f}s")
                new_end = nearest_end_cut

        # 3. [NEW] Phase 4: Dynamic Padding (Breathing Room)
        # 0.15s start (inhalation), 0.2s end (trailing thought)
        new_start = max(0, new_start - 0.15)
        new_end = new_end + 0.2
        
        # 4. [NEW] Stop-word Trimming
        # If Phase 2 flagged a stop-word at the end, we retroactively trim the end time 
        # to the end of the second-to-last word cluster
        if clip.get('has_stopword'):
            print(f"  ✂️ Trimming stop-word tail from end boundary.")
            new_end -= 0.8 # Empirical trim to remove "y bueno..." etc.

        # Ensure minimum duration
        if (new_end - new_start) < 5.0:
            new_end = new_start + 10.0
            
        refined_clip = clip.copy()
        refined_clip['start_time'] = round(new_start, 2)
        refined_clip['end_time'] = round(new_end, 2)
        refined_clip['original_start'] = orig_start
        refined_clip['original_end'] = orig_end
        
        print(f"✅ Adjusted \"{clip['title']}\": {orig_start}s->{refined_clip['start_time']}s | {orig_end}s->{refined_clip['end_time']}s (Duration: {refined_clip['end_time']-refined_clip['start_time']:.1f}s)")
        refined_clips.append(refined_clip)
        
    return refined_clips

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clips', required=True)
    parser.add_argument('--words', required=True)
    parser.add_argument('--video', required=False)
    parser.add_argument('--silences', required=False)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    
    with open(args.clips, 'r', encoding='utf-8') as f:
        clips = json.load(f)
        # Handle different output formats from Gemini
        if isinstance(clips, dict) and 'clips' in clips:
            clips = clips['clips']
            
    with open(args.words, 'r', encoding='utf-8') as f:
        word_data = json.load(f)
        # Handle Whisper JSON format (words nested in segments)
        if isinstance(word_data, dict) and 'segments' in word_data:
            words = []
            for seg in word_data['segments']:
                if 'words' in seg:
                    words.extend(seg['words'])
                else:
                    words.append({'word': seg.get('text', ''), 'start': seg.get('start', 0), 'end': seg.get('end', 0)})
        elif isinstance(word_data, dict) and 'words' in word_data:
            words = word_data['words']
        elif isinstance(word_data, list):
            words = word_data
        else:
            words = []
            
    silences = []
    if args.silences and os.path.exists(args.silences):
        with open(args.silences, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Use full silence segments for duration-aware snapping
            silences = data.get('silences', [])
            if not silences and 'boundary_points' in data:
                # Fallback if only points are present
                silences = [{'start': p, 'end': p, 'duration': 0.0} for p in data['boundary_points']]
            
    refined = refine_clips(clips, words, args.video, silences)
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({'clips': refined}, f, indent=2)
        
    print(f"💾 Refined clips saved to: {args.output}")

if __name__ == "__main__":
    main()
