"""
YouTube Automation Pro — CLI Entry Point
Quick commands to run the system.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="YouTube Automation Pro CLI")
    parser.add_argument("command", choices=["server", "generate", "trends", "ideas", "setup-db"],
                        help="Command to run")
    parser.add_argument("--channel", type=str, help="Channel ID (e.g., impacto-mundial)")
    parser.add_argument("--topic", type=str, help="Video topic")
    parser.add_argument("--upload", action="store_true", help="Upload to YouTube after generation")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    args = parser.parse_args()

    if args.command == "server":
        import uvicorn
        print("🚀 Starting YouTube Automation Pro server...")
        uvicorn.run("backend.server:app", host=args.host, port=args.port, reload=True)

    elif args.command == "setup-db":
        from backend.database import init_db
        init_db()
        print("✅ Database initialized with 6 channels.")

    elif args.command == "generate":
        if not args.channel:
            print("❌ --channel is required for generate command")
            sys.exit(1)
        from backend.pipeline.orchestrator import run_single_channel
        result = run_single_channel(args.channel, topic=args.topic, upload=args.upload)
        status = result.get("status", "unknown")
        print(f"\n{'✅' if status == 'ok' else '❌'} Pipeline result: {status}")
        if result.get("error"):
            print(f"   Error: {result['error']}")

    elif args.command == "trends":
        from backend.database import get_channel, init_db
        init_db()
        channel_id = args.channel or "impacto-mundial"
        ch = get_channel(channel_id)
        if not ch:
            print(f"❌ Channel not found: {channel_id}")
            sys.exit(1)
        from backend.pipeline.trend_finder import find_trending_topics
        trends = find_trending_topics(ch)
        for t in trends:
            print(f"  [{t.get('score', 0):.0f}] {t.get('topic', '')}")

    elif args.command == "ideas":
        from backend.database import init_db
        init_db()
        from backend.pipeline.idea_engine import generate_ideas_for_channel, generate_ideas_all_channels
        channel_id = args.channel
        if channel_id:
            print(f"Generating ideas for {channel_id}...")
            result = generate_ideas_for_channel(channel_id)
            print(f"\n{result['total_generated']} ideas generated, {result['new_saved']} new saved\n")
            print("TOP 5 IDEAS:")
            for i, idea in enumerate(result.get("top_5", []), 1):
                score = idea.get("virality_score", 0)
                print(f"  {i}. [{score:.0f}] {idea.get('title', '')}")
                if idea.get("hook"):
                    print(f"     Hook: {idea['hook']}")
        else:
            print("Generating ideas for ALL 6 channels...")
            results = generate_ideas_all_channels()
            for ch_id, r in results.items():
                if "error" in r:
                    print(f"  {ch_id}: ERROR - {r['error']}")
                else:
                    print(f"  {ch_id}: {r.get('total_generated', 0)} ideas")


if __name__ == "__main__":
    main()
