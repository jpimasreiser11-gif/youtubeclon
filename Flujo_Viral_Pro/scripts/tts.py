import asyncio
import edge_tts
import argparse

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--voice", default="es-ES-AlvaroNeural")
    parser.add_argument("--rate", default="+10%")
    args = parser.parse_args()

    communicate = edge_tts.Communicate(args.text, args.voice, rate=args.rate)
    await communicate.save(args.output)
    print(f"Audio saved to {args.output}")

if __name__ == "__main__":
    asyncio.run(main())
