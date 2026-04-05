def add_transformative_value(segment_text, topic, angle):
    try:
        import ollama
        prompt = (
            f'Contenido original: "{segment_text}"\n'
            f'Escribe comentario de 15-25 palabras que anada contexto sobre {topic} '
            f'desde el angulo: {angle}. Solo texto.'
        )
        response = ollama.chat(model="mistral", messages=[{"role": "user", "content": prompt}])
        return response["message"]["content"].strip()
    except Exception:
        return f"Lo importante aqui es el contexto que no se cuenta: aplicado a {topic}, este punto cambia tus decisiones." 
