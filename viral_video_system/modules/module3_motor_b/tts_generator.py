import os


def tts_xtts_remote(text, output_path, language="es", voice_name="default"):
    """Call a remote XTTS-v2 service endpoint if configured.

    Expected env vars:
    - XTTS_API_URL: base endpoint (example: http://server:8020/tts)
    - XTTS_API_KEY: optional bearer token
    """
    api_url = os.getenv("XTTS_API_URL", "").strip()
    if not api_url:
        return None

    try:
        import requests

        headers = {"Content-Type": "application/json"}
        api_key = os.getenv("XTTS_API_KEY", "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "text": text,
            "language": language,
            "voice": voice_name,
        }
        resp = requests.post(api_url, json=payload, headers=headers, timeout=120)
        resp.raise_for_status()

        ctype = (resp.headers.get("Content-Type") or "").lower()
        if "audio" in ctype:
            with open(output_path, "wb") as f:
                f.write(resp.content)
            return output_path

        data = resp.json() if resp.text else {}
        audio_url = (data or {}).get("audio_url")
        if audio_url:
            dl = requests.get(audio_url, timeout=120)
            dl.raise_for_status()
            with open(output_path, "wb") as f:
                f.write(dl.content)
            return output_path
    except Exception:
        return None

    return None


def tts_edge(text, output_path, voice="es-ES-AlvaroNeural", rate="+10%", pitch="-5Hz"):
    # Prefer XTTS-v2 if configured remotely; fallback to Edge for resilience.
    xtts_lang = "en" if "en-" in str(voice).lower() else "es"
    xtts_audio = tts_xtts_remote(text=text, output_path=output_path, language=xtts_lang, voice_name=voice)
    if xtts_audio:
        return xtts_audio

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
