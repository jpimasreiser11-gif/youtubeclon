import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def analyze_channel_style(channel_info):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Estilo generico debido a falta de API Key."

    genai.configure(api_key=api_key)
    # Use gemini-1.5-flash for stability/cost
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt = f"""
    Actua como un experto productor de documentales de YouTube.
    Analiza la siguiente informacion de un canal y genera un 'System Prompt' detallado para el guionista.
    
    Informacion del Canal:
    Nombre: {channel_info.get('name')}
    Tema: {channel_info.get('topic')}
    Tono: {channel_info.get('tone')}
    Audiencia: {channel_info.get('target_audience')}

    El Output debe ser instruccional para una IA que escribira el guion.
    Ejemplo de output esperado:
    "Eres el guionista principal de 'Misterios Sombrios'. Tu estilo es lento y pausado. Usas palabras como 'escalofriante' y 'perturbador'. Nunca saludas con 'Hola chicos', entras directo a la accion..."
    """

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error generando estilo: {str(e)}"

if __name__ == "__main__":
    # Test
    sample = {
        "name": "Test Channel",
        "topic": "Historia Antigua",
        "tone": "Epico y Academico",
        "target_audience": "Estudiantes"
    }
    print(analyze_channel_style(sample))
