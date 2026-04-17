
import asyncio
import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from pipeline.generador_guion import generate_script_json
from backend.database import init_db, get_all_channels

# Initial topics for each channel to "seed" the network
TOPICS = {
    "impacto-mundial": [
        "El incidente de la Antártida que fue borrado de los mapas",
        "Documentos desclasificados sobre la ciudad subterránea de Derinkuyu",
        "El misterio del vuelo 370: lo que los radares militares ocultaron"
    ],
    "mentes-rotas": [
        "El caso del 'Carnicero de Milwaukee': las señales que la policía ignoró",
        "La desaparición de Madeleine McCann: nuevas evidencias 2026",
        "Pecados de familia: El caso de los hermanos Menéndez"
    ],
    "el-loco-de-la-ia": [
        "Cómo crear una agencia de automatización con IA en 2026",
        "Guía definitiva de Sora 2.0: Generación de video hiperrealista",
        "3 Herramientas de IA gratis que reemplazan a todo el equipo de marketing"
    ],
    "mind-warp": [
        "The Stanford Prison Experiment: What they didn't tell you in school",
        "Dark Psychology: 5 subtle signs someone is manipulating your thoughts",
        "The Mandela Effect: Proof of parallel universes or collective failure?"
    ],
    "wealth-files": [
        "How BlackRock actually controls the world's economy",
        "The 'Buy, Borrow, Die' strategy used by the 0.01%",
        "Why 99% of startups fail and the one thing that saves the rest"
    ],
    "dark-science": [
        "The James Webb discovery that broke physics: what NASA is hiding",
        "Oceanic anomalies: the sound from the abyss that isn't biological",
        "Quantum entanglement and the proof of a simulation"
    ]
}

async def run_batch():
    init_db()
    channels = get_all_channels()
    active_channel_ids = [c["channel_id"] for c in channels if c.get("is_active", 1)]
    
    print(f"Starting Batch Production for {len(active_channel_ids)} channels...")
    
    for channel_id in active_channel_ids:
        if channel_id not in TOPICS:
            continue
            
        print(f"Processing Channel: {channel_id}")
        for i, topic in enumerate(TOPICS[channel_id]):
            print(f"Generating Script {i+1}/3: {topic}")
            try:
                # We use 'auto' to use Gemini if available, or fallback to local
                result = generate_script_json(topic=topic, channel_id=channel_id, script_provider="auto")
                print(f"Success! Title: {result['script']['title']}")
            except Exception as e:
                print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_batch())
