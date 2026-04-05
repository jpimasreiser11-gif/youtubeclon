import sys
import os
import json
import random
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def generate_idea():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        # Fallback Mock
        return {
            "nicho": "Datos Curiosos de la Mente",
            "script_text": "Sabias que tu cerebro toma decisiones 7 segundos antes de que seas consciente de ellas? Es como si vivieras en el pasado. Sigueme para mas.",
            "keywords": "brain psychology abstract"
        }

    genai.configure(api_key=api_key)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = """
        Genera una idea para un video viral de TikTok corto (max 60 palabras).
        Formato JSON:
        {
            "nicho": "Tema general",
            "script_text": "El guion exacto para ser leido",
            "keywords": "3 palabras clave en ingles para buscar video de stock"
        }
        """

        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})

        return json.loads(response.text)
    except Exception as e:
        sys.stderr.write(f"Warning: API Error ({str(e)}). Using random fallback idea.\\n")
        
        fallback_ideas = [
            {
                "nicho": "Datos Curiosos de la Mente",
                "script_text": "Sabias que tu cerebro toma decisiones 7 segundos antes de que seas consciente de ellas? Es como si vivieras en el pasado. Sigueme para mas.",
                "keywords": "brain psychology abstract"
            },
            {
                "nicho": "Misterios del Espacio",
                "script_text": "Si gritas en el espacio, nadie te oye. No porque no haya nadie, sino porque el sonido no viaja en el vacio. El silencio mas aterrador del universo.",
                "keywords": "space universe dark"
            },
            {
                "nicho": "Paradojas Temporales",
                "script_text": "Imagina que viajas al pasado y matas a tu abuelo. Entonces no naces. Entonces no viajas. Entonces no lo matas. La paradoja del abuelo te hara explotar la cabeza.",
                "keywords": "time travel clock mystery"
            },
            {
                "nicho": "Psicologia Oscura",
                "script_text": "El efecto Ben Franklin dice que si le haces un favor a alguien, te caera mejor. Usalo con cuidado para manipular... digo, hacer amigos.",
                "keywords": "psychology manipulation dark"
            },
            {
                "nicho": "Futuro IA",
                "script_text": "La Inteligencia Artificial ya puede clonar tu voz con 3 segundos de audio. En el futuro, no sabras si hablas con tu madre o con un robot.",
                "keywords": "artificial intelligence robot future"
            }
        ]
        return random.choice(fallback_ideas)

if __name__ == "__main__":
    idea = generate_idea()
    print(json.dumps(idea))
