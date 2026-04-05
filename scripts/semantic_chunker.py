import spacy
import json
import argparse
from typing import List, Dict

def load_spacy_model():
    print("🧠 Loading Spacy model (es_core_news_sm)...")
    try:
        return spacy.load("es_core_news_sm")
    except OSError:
        print("⚠️ Model not found. downloading...")
        from spacy.cli import download
        download("es_core_news_sm")
        return spacy.load("es_core_news_sm")

def chunk_transcript(words: List[Dict]) -> List[Dict]:
    """
    Groups word-level timestamps into logical sentences using NLP.
    Returns a list of Sentence Blocks:
    {
        'id': 1,
        'text': "Hola amigos, bienvenidos.",
        'start': 0.0,
        'end': 2.5,
        'words': [...]
    }
    """
    nlp = load_spacy_model()
    
    # 1. Reconstruct full text to let Spacy see the context
    full_text = ""
    # We need to map character positions back to words to recover timestamps
    char_to_word_index = [] 
    
    current_pos = 0
    for i, w in enumerate(words):
        word_text = w['word']
        # Add space if not first word and not punctuation (heuristic)
        prefix = " " if i > 0 else ""
        
        full_text += prefix + word_text
        
        # Map every character in this word to the word index
        # prefix len
        for _ in range(len(prefix)):
            char_to_word_index.append(None) # Space has no word index
            
        for _ in range(len(word_text)):
            char_to_word_index.append(i)
            
    # 2. Process with Spacy
    doc = nlp(full_text)
    
    sentences = []
    
    for sent_id, sent in enumerate(doc.sents):
        # recover start/end times from word mapping
        sent_start_char = sent.start_char
        sent_end_char = sent.end_char
        
        # Find first valid word index in this range
        start_word_idx = None
        for c in range(sent_start_char, sent_end_char):
            if c < len(char_to_word_index) and char_to_word_index[c] is not None:
                start_word_idx = char_to_word_index[c]
                break
                
        # Find last valid word index
        end_word_idx = None
        for c in range(sent_end_char - 1, sent_start_char - 1, -1):
            if c < len(char_to_word_index) and char_to_word_index[c] is not None:
                end_word_idx = char_to_word_index[c]
                break
        
        if start_word_idx is not None and end_word_idx is not None:
            # Extract timestamps
            start_time = words[start_word_idx]['start']
            end_time = words[end_word_idx]['end']
            
            # Get words in this sentence
            sent_words = words[start_word_idx : end_word_idx + 1]
            
            sentences.append({
                'id': sent_id + 1,
                'text': sent.text.strip(),
                'start': start_time,
                'end': end_time,
                'word_count': len(sent_words)
            })
            
    return sentences

import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

load_dotenv()

def group_into_topics(sentences: List[Dict]) -> List[Dict]:
    """
    Phase 1: Groups sentences into logical 'Topic Blocks' or 'Chapters' using Gemini.
    """
    print("🔮 Identifying logical topics/chapters...")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️ No GEMINI_API_KEY found, skipping topic grouping.")
        return sentences

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')

    transcript_text = "\n".join([f"[{s['id']}] {s['text']}" for s in sentences])
    
    prompt = f"""
    DIVIDE ESTE TEXTO EN CAPÍTULOS O TEMAS LÓGICOS.
    Cada capítulo debe agrupar oraciones que hablen de lo mismo.
    
    TEXTO:
    {transcript_text}
    
    RESPONDE ÚNICAMENTE CON UN JSON:
    [
      {{
        "topic": "Nombre del tema",
        "start_id": 1,
        "end_id": 5
      }}
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            topics = json.loads(json_match.group(0))
            for topic in topics:
                # Assign topic info to belonging sentences
                for s in sentences:
                    if topic['start_id'] <= s['id'] <= topic['end_id']:
                        s['topic'] = topic['topic']
                        s['topic_start'] = topic['start_id']
                        s['topic_end'] = topic['end_id']
            print(f"✅ Grouped into {len(topics)} topics.")
    except Exception as e:
        print(f"⚠️ Topic grouping failed: {e}")
    
    return sentences

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--words', required=True, help="JSON file with word-level timestamps")
    parser.add_argument('--output', required=True, help="Output JSON for sentence blocks")
    parser.add_argument('--group-topics', action='store_true', help="Use Gemini to group into chapters")
    args = parser.parse_args()
    
    with open(args.words, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if isinstance(data, dict):
            words = data.get('words', [])
            if not words and 'segments' in data:
                for seg in data['segments']:
                    words.extend(seg.get('words', []))
        else:
            words = data
            
    sentences = chunk_transcript(words)
    
    if args.group_topics:
        sentences = group_into_topics(sentences)
    
    print(f"✅ Processed {len(sentences)} semantic sentences")
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump({'sentences': sentences}, f, indent=2, ensure_ascii=False)
