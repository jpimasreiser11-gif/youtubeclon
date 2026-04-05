import asyncio
import edge_tts
import argparse
import os

# Configuración de perfiles de voz por nicho
VOICE_PROFILES = {
    "mystery": {
        "voice": "en-US-ChristopherNeural", # Voz masculina profunda
        "pitch": "-5Hz",                    # Bajar el tono para seriedad
        "rate": "-10%"                      # Hablar más lento para suspenso
    },
    "history": {
        "voice": "en-GB-RyanNeural",       # Acento británico académico
        "pitch": "-2Hz",
        "rate": "0%"
    },
    "tech": {
        "voice": "en-US-AriaNeural",        # Voz femenina clara y moderna
        "pitch": "+0Hz",
        "rate": "+5%"                       # Ritmo rápido y dinámico
    }
}

async def generate_audio(text, output_file, niche="mystery"):
    print(f"Generating audio for niche: {niche}")
    profile = VOICE_PROFILES.get(niche, VOICE_PROFILES["mystery"])
    print(f"Using profile: {profile['voice']} (Pitch: {profile['pitch']}, Rate: {profile['rate']})")
    
    # Ensure output directory exists (if path has directory)
    if os.path.dirname(output_file):
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    try:
        communicate = edge_tts.Communicate(
            text, 
            profile["voice"], 
            pitch=profile["pitch"], 
            rate=profile["rate"]
        )
        await communicate.save(output_file)
        print(f"Audio saved to: {output_file}")
        return output_file
    except Exception as e:
        print(f"Error in edge-tts: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--niche", default="mystery")
    args = parser.parse_args()
    
    # Run async function
    loop = asyncio.get_event_loop_policy().get_event_loop()
    try:
        loop.run_until_complete(generate_audio(args.text, args.out, args.niche.lower()))
    except Exception as e:
        print(f"Critical Error: {e}")
