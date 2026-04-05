#!/usr/bin/env python3
"""Compatibility bridge to run the new architecture without replacing old flow."""
import argparse
import os
import sys
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from viral_video_system.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--niche", default="finanzas personales")
    parser.add_argument("--mode", default="auto", choices=["auto", "motor_a", "motor_b"])
    parser.add_argument("--dry-run", action="store_true", default=False)
    parser.add_argument("--youtube-creds-file", default="")
    parser.add_argument("--input-json", default="")
    parser.add_argument("--trend-mode", default="internet", choices=["internet", "manual-only"])
    args = parser.parse_args()

    youtube_credentials = None
    seed_input = None
    if args.youtube_creds_file:
        try:
            with open(args.youtube_creds_file, "r", encoding="utf-8") as f:
                youtube_credentials = json.load(f)
        except Exception as e:
            print(f"Warning: could not load YouTube credentials file: {e}")

    if args.input_json:
        try:
            seed_input = json.loads(args.input_json)
        except Exception as e:
            print(f"Warning: could not parse --input-json payload: {e}")

    out_json, result = run_pipeline(
        niche=args.niche,
        mode=args.mode,
        dry_run=args.dry_run,
        youtube_credentials=youtube_credentials,
        seed_input=seed_input,
        trend_mode=args.trend_mode,
    )
    print(f"Bridge done. Output: {out_json}")
    print(f"Selected mode: {result['selected_mode']}")


if __name__ == "__main__":
    main()
