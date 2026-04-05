#!/usr/bin/env python3
"""
Dry-run helper: score and preview results for a local video without DB.
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
import re
from collections import Counter

ROOT_DIR = str(Path(__file__).parent.parent.parent)

# Minimal STOPWORDS (reused from ingest helpers)
STOPWORDS = set([
    'the','that','have','this','with','from','they','will','would','there','their','about','which','when','what','where','who','how','why','your','you','for','and','but','not','are','was','were','been','is','a','an','in','on','at','of','to',
    'que','por','para','con','sin','sobre','entre','como','pero','como','más','menos','esta','este','estos','estas','usted','tu','tú','las','los','un','una','unos','unas'
])


def words_to_text(words):
    if not words:
        return ''
    if isinstance(words, str):
        return words
    parts = []
    for w in words:
        if isinstance(w, str):
            parts.append(w)
        elif isinstance(w, dict):
            t = w.get('text') or w.get('word') or w.get('token') or w.get('value')
            if t:
                parts.append(str(t))
        else:
            parts.append(str(w))
    return ' '.join(parts)


def extract_keywords(text, n=5):
    if not text:
        return []
    text_low = text.lower()
    text_clean = re.sub(r'[^a-z0-9áéíóúüñ\s]', ' ', text_low)
    tokens = [t for t in text_clean.split() if len(t) > 3 and t not in STOPWORDS]
    if not tokens:
        return []
    counts = Counter(tokens)
    return [w for w,_ in counts.most_common(n)]


def detect_hook(text):
    if not text:
        return ''
    parts = re.split(r'[\.\!\?\n]+', text.strip())
    if not parts:
        return ''
    first = parts[0].strip()
    if not first:
        return ''
    qwords = ['what','how','why','when','where','who','do','did','¿','por','cómo','qué','por qué','quién']
    for q in qwords:
        if q in first.lower():
            return first
    words = first.split()
    return ' '.join(words[:12])


def generate_title(text, meta=None, max_len=60):
    if meta and meta.get('title'):
        return meta.get('title')[:max_len]
    hook = detect_hook(text)
    if hook:
        return hook[:max_len]
    kws = extract_keywords(text, n=3)
    if kws:
        return ' '.join(kws).title()[:max_len]
    words = text.split()
    return ' '.join(words[:8])[:max_len]


def score_and_enrich_results(results):
    enriched = []
    for res in results:
        meta = (res.get('metadata') or {})
        words_list = res.get('words', [])
        transcript = words_to_text(words_list)
        base = int(meta.get('virality_score', 50)) if meta.get('virality_score') is not None else 50
        duration = float(res.get('duration') or 0)
        score = base
        if 8 <= duration <= 25:
            score += 12
        elif 25 < duration <= 45:
            score += 5
        elif duration < 6:
            score -= 15
        elif duration > 60:
            score -= int((duration - 60) / 2)
        hook = meta.get('hook') or detect_hook(transcript)
        if hook:
            score += 15
            meta['hook'] = hook
        keywords = extract_keywords(transcript, n=5)
        if keywords:
            score += min(10, len(keywords) * 2)
            meta['hashtags'] = ' '.join('#' + k for k in keywords[:5])
        else:
            meta['hashtags'] = ''
        tokens = re.findall(r'\w+', transcript.lower())
        unique_ratio = len(set(tokens)) / max(1, len(tokens))
        score += int(unique_ratio * 5)
        score = max(0, min(100, int(score)))
        meta['composite_score'] = score
        meta['title'] = meta.get('title') or generate_title(transcript, meta)
        res['metadata'] = meta
        enriched.append(res)
    enriched.sort(key=lambda r: r.get('metadata', {}).get('composite_score', 0), reverse=True)
    return enriched


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', help='Path to local video for dry-run')
    parser.add_argument('--out', help='Output JSON file', default=None)
    args = parser.parse_args()

    source = args.video
    if not source or not os.path.exists(source):
        print('No local video provided or not found. Provide --video path to a local mp4 to dry-run.')
        sys.exit(1)

    # Build a fake result structure that resembles engine output
    fake_words = [{'text': 'Este es un clip de prueba con contenido sorprendente para captar la atención del público.'}]
    fake_res = {
        'path': os.path.abspath(source),
        'duration': 18,
        'words': fake_words,
        'metadata': {
            'virality_score': 65,
            'title': None,
            'description': None,
            'hook': None
        }
    }

    enriched = score_and_enrich_results([fake_res])

    out_dir = os.path.join(ROOT_DIR, 'app', 'storage', 'test_runs')
    os.makedirs(out_dir, exist_ok=True)
    ts = int(time.time())
    out_file = args.out or os.path.join(out_dir, f'results_{ts}.json')

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

    print(f'Wrote dry-run results to: {out_file}')
    top = enriched[0]['metadata'] if enriched else None
    if top:
        print('Top clip title:', top.get('title'))
        print('Composite score:', top.get('composite_score'))
    else:
        print('No clips generated in dry-run')
