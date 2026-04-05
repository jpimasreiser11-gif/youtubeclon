import os


def tts_edge(text, output_path, voice="es-ES-AlvaroNeural", rate="+10%", pitch="-5Hz"):
    try:
        import asyncio
        import edge_tts

        async def _gen():
            communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
            await communicate.save(output_path)

        asyncio.run(_gen())
        return output_path
    except Exception:
        # Fallback sin romper flujo: guardar texto como referencia
        txt_path = output_path + ".txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        return txt_path


def tts_coqui_local(text, output_path):
    try:
        from TTS.api import TTS
        tts = TTS("tts_models/es/css10/vits", progress_bar=False)
        tts.tts_to_file(text=text, file_path=output_path)
        return output_path
    except Exception:
        txt_path = output_path + ".txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(text)
        return txt_path
