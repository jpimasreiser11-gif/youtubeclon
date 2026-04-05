"""
Auto-SEO Generator: Títulos, Descripciones y Hashtags Virales
Usa Gemini para generar metadata optimizada automáticamente
"""

import os
import sys
import json
from typing import Dict, List
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_seo_metadata(
    hook_description: str,
    payoff_description: str,
    category: str,
    duration: float
) -> Dict[str, any]:
    """
    Genera metadata SEO optimizada usando Gemini
    
    Args:
        hook_description: Por qué el inicio engancha
        payoff_description: Resolución del clip
        category: Categoría del clip
        duration: Duración en segundos
    
    Returns:
        Dict con title, description, hashtags
    """
    print("🤖 Generando SEO con Gemini...")
    
    prompt = f"""Eres un experto en marketing viral para redes sociales. Genera metadata SEO optimizada para este clip:

INFORMACIÓN DEL CLIP:
- Gancho: {hook_description}
- Resolución: {payoff_description}
- Categoría: {category}
- Duración: {int(duration)}s

GENERA:
1. Un título viral (máximo 60 caracteres)
   - Debe crear curiosidad sin ser clickbait extremo
   - Incluir números si es relevante
   - Primera palabra debe captar atención
   
2. Una descripción optimizada para YouTube Shorts/TikTok (150 caracteres)
   - Resume el valor del clip
   - Incluye keywords relevantes
   - Call-to-action sutil
   
3. 5 hashtags estratégicos
   - 2 hashtags amplios (#viral, #shorts)
   - 3 hashtags específicos de la categoría/tema

DEVUELVE SOLO JSON:
{{
    "title": "título aquí",
    "description": "descripción aquí",
    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5"]
}}

IMPORTANTE: El título NO debe revelar completamente el payoff, debe generar curiosidad.
"""
    
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = await model.generate_content_async(prompt)
    
    try:
        # Extraer JSON
        text = response.text
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        
        metadata = json.loads(text.strip())
        
        # Validar longitudes
        if len(metadata['title']) > 60:
            metadata['title'] = metadata['title'][:57] + '...'
        
        if len(metadata['description']) > 150:
            metadata['description'] = metadata['description'][:147] + '...'
        
        print(f"✓ SEO generado:")
        print(f"  Título: {metadata['title']}")
        print(f"  Hashtags: {', '.join(metadata['hashtags'])}")
        
        return metadata
        
    except Exception as e:
        print(f"⚠️ Error generando SEO: {e}")
        # Fallback básico
        return {
            "title": f"{category}: {hook_description[:40]}...",
            "description": f"{hook_description} {payoff_description}"[:150],
            "hashtags": ["#viral", "#shorts", f"#{category.lower()}", "#trending", "#foryou"]
        }

async def batch_generate_seo(clips: List[Dict]) -> List[Dict]:
    """
    Genera SEO para múltiples clips en batch
    
    Args:
        clips: Lista de clips con hook/payoff/category
    
    Returns:
        Lista de clips con metadata SEO añadida
    """
    print(f"\n📊 Generando SEO para {len(clips)} clips...\n")
    
    for i, clip in enumerate(clips):
        print(f"[{i+1}/{len(clips)}] Procesando clip: {clip.get('title', 'Sin título')[:30]}...")
        
        metadata = await generate_seo_metadata(
            hook_description=clip.get('hook_description', ''),
            payoff_description=clip.get('payoff_description', ''),
            category=clip.get('category', 'Otro'),
            duration=clip.get('end_time', 0) - clip.get('start_time', 0)
        )
        
        # Añadir metadata al clip
        clip['title_generated'] = metadata['title']
        clip['description_generated'] = metadata['description']
        clip['hashtags'] = metadata['hashtags']
    
    print("\n✅ SEO generado para todos los clips\n")
    return clips

# CLI para testing
if __name__ == "__main__":
    import asyncio
    
    # Test
    test_clip = {
        'hook_description': 'Reacción inesperada cuando le preguntamos sobre su pasado',
        'payoff_description': 'La historia emocional detrás de su decisión que cambió todo',
        'category': 'Inspiracional',
        'start_time': 10.0,
        'end_time': 55.0
    }
    
    result = asyncio.run(generate_seo_metadata(
        test_clip['hook_description'],
        test_clip['payoff_description'],
        test_clip['category'],
        test_clip['end_time'] - test_clip['start_time']
    ))
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
