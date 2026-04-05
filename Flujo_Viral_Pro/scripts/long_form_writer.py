import os
import json
import time
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def config_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise Exception("API Key Missing")
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def generate_outline(topic, channel_style, model):
    prompt = f"""
    {channel_style}
    
    Tu tarea es crear un OUTLINE (Estructura) para un documental de 15 minutos sobre: "{topic}".
    El video debe ser altamente adictivo y retener la atencion.
    
    Genera un JSON con la siguiente estructura:
    {{
        "title": "Titulo Clickbait del Video",
        "thumbnail_idea": "Descripcion visual para la miniatura",
        "sections": [
            {{ "title": "Intro: El Gancho", "duration_seconds": 60, "objective": "Atrapar al espectador con una pregunta imposible" }},
            {{ "title": "Capitulo 1: El Contexto", "duration_seconds": 180, "objective": "Explicar el background..." }},
            ...
            {{ "title": "Conclusion: El Giro Final", "duration_seconds": 120, "objective": "Dejar al espectador pensando" }}
        ]
    }}
    """
    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        return json.loads(response.text)
    except Exception as e:
        print(f"Error generando outline: {e}")
        return None

def write_section(section, topic, channel_style, model):
    prompt = f"""
    {channel_style}
    
    Estamos escribiendo un documental sobre: "{topic}".
    
    Escribe el GUION COMPLETO para la seccion: "{section['title']}".
    Objetivo de esta seccion: "{section['objective']}".
    Duracion estimada: {section['duration_seconds']} segundos.
    
    Formato de salida (Texto Plano):
    Escribe el guion tal cual lo debe leer el narrador. Usa frases cortas. No pongas acotaciones como (Musica de fondo) o [Narrador]. Solo el texto hablado.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error escribiendo seccion {section['title']}: {e}")
        return ""

def generate_full_script(topic, channel_style_prompt):
    model = config_gemini()
    
    print(f"1. Generando Estructura para: {topic}...")
    outline = generate_outline(topic, channel_style_prompt, model)
    if not outline:
        return None
        
    print(f"   Titulo generad: {outline['title']}")
    
    full_script = []
    
    for i, section in enumerate(outline['sections']):
        print(f"2. Escribiendo Seccion {i+1}/{len(outline['sections'])}: {section['title']}...")
        text = write_section(section, topic, channel_style_prompt, model)
        
        section_data = {
            "title": section['title'],
            "duration": section['duration_seconds'],
            "text": text,
            "visual_keywords": f"{topic} {section['title']} visual" # Placeholder for now
        }
        full_script.append(section_data)
        time.sleep(1) # Avoid rate limit burst
        
    final_output = {
        "meta": outline,
        "script_blocks": full_script
    }
    
    return final_output

if __name__ == "__main__":
    # Test
    style = "Eres un narrador de misterios. Tu voz es grave. Te centras en lo desconocido."
    script = generate_full_script("El incidente del Paso Dyatlov", style)
    
    # Save test
    with open("temp/long_script_test.json", "w", encoding='utf-8') as f:
        json.dump(script, f, indent=2, ensure_ascii=False)
    print("Test completado. Guardado en temp/long_script_test.json")
