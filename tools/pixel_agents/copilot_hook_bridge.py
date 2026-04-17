"""
Send Copilot CLI lifecycle events to Pixel Agents server.

Usage examples:
  python tools/pixel_agents/copilot_hook_bridge.py session-start --session-id abc --cwd C:\\work
  python tools/pixel_agents/copilot_hook_bridge.py stop --session-id abc
  python tools/pixel_agents/copilot_hook_bridge.py session-end --session-id abc --reason exit
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib import request


def _server_config_path() -> Path:
    return Path.home() / ".pixel-agents" / "server.json"


def _load_server_config() -> dict:
    path = _server_config_path()
    if not path.exists():
        raise FileNotFoundError(f"Pixel Agents server config not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _post_event(event: dict) -> None:
    cfg = _load_server_config()
    port = int(cfg["port"])
    token = str(cfg["token"])
    url = f"http://127.0.0.1:{port}/api/hooks/copilot"
    data = json.dumps(event).encode("utf-8")
    req = request.Request(
        url=url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    with request.urlopen(req, timeout=2):
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="Copilot -> Pixel Agents hook bridge")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_start = sub.add_parser("session-start")
    p_start.add_argument("--session-id", required=True)
    p_start.add_argument("--cwd", default=os.getcwd())

    p_stop = sub.add_parser("stop")
    p_stop.add_argument("--session-id", required=True)

    p_end = sub.add_parser("session-end")
    p_end.add_argument("--session-id", required=True)
    p_end.add_argument("--reason", default="exit")

    args = parser.parse_args()

    if args.cmd == "session-start":
        event = {
            "hook_event_name": "SessionStart",
            "session_id": args.session_id,
            "source": "new",
            "cwd": args.cwd,
        }
    elif args.cmd == "stop":
        event = {
            "hook_event_name": "Stop",
            "session_id": args.session_id,
            "stop_hook_active": False,
        }
    else:
        event = {
            "hook_event_name": "SessionEnd",
            "session_id": args.session_id,
            "reason": args.reason,
        }

    _post_event(event)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
