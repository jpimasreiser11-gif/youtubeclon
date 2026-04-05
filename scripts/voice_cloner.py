import asyncio
import edge_tts
import argparse
import json

# List of realistic Spanish voices
# es-ES-AlvaroNeural (Male)
# es-ES-ElviraNeural (Female)
# es-MX-DaliaNeural (Female)
# es-MX-JorgeNeural (Male)

async def generate_voice(text, output_file, voice="es-ES-AlvaroNeural"):
    """Generate high-quality speech using Microsoft Edge TTS API (Free)"""
    print(f"🎙️ Generating voiceover with edge-tts ({voice})...")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    return output_file

async def list_voices():
    voices = await edge_tts.VoicesManager.create()
    return voices.find(Language="es")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--voice", default="es-ES-AlvaroNeural")
    parser.add_argument("--list", action="store_true")
    
    args = parser.parse_args()
    
    if args.list:
        loop = asyncio.get_event_loop()
        voices = loop.run_until_complete(list_voices())
        print(json.dumps(voices, indent=2))
    else:
        asyncio.run(generate_voice(args.text, args.output, args.voice))
        print(f"✅ Voiceover saved to: {args.output}")
