from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from backend.database import get_channel, get_db, init_db

AFFILIATE_SCHEMA = """
CREATE TABLE IF NOT EXISTS affiliate_links (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id      INTEGER NOT NULL REFERENCES channels(id),
    campaign_name   TEXT NOT NULL,
    partner_name    TEXT NOT NULL,
    destination_url TEXT NOT NULL,
    tracking_code   TEXT NOT NULL,
    is_active       INTEGER DEFAULT 1,
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS affiliate_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    link_id         INTEGER NOT NULL REFERENCES affiliate_links(id),
    channel_id      INTEGER NOT NULL REFERENCES channels(id),
    event_type      TEXT NOT NULL CHECK(event_type IN ('click', 'conversion')),
    video_id        INTEGER REFERENCES videos(id),
    event_value     REAL DEFAULT 0,
    event_count     INTEGER DEFAULT 1,
    event_ts        TEXT DEFAULT (datetime('now')),
    notes           TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_affiliate_links_channel ON affiliate_links(channel_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_events_link ON affiliate_events(link_id);
CREATE INDEX IF NOT EXISTS idx_affiliate_events_channel_type ON affiliate_events(channel_id, event_type);
"""


def ensure_affiliate_tables() -> None:
    init_db()
    with get_db() as conn:
        conn.executescript(AFFILIATE_SCHEMA)


def add_link(channel_slug: str, campaign: str, partner: str, url: str, tracking_code: str) -> dict:
    if not all([channel_slug.strip(), campaign.strip(), partner.strip(), url.strip(), tracking_code.strip()]):
        raise ValueError("channel, campaign, partner, url and tracking_code are required")
    ensure_affiliate_tables()
    channel = get_channel(channel_slug)
    if not channel:
        raise ValueError(f"Unknown channel: {channel_slug}")
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO affiliate_links (channel_id, campaign_name, partner_name, destination_url, tracking_code)
            VALUES (?, ?, ?, ?, ?)
            """,
            (channel["id"], campaign, partner, url, tracking_code),
        )
        link_id = cur.lastrowid
    return {"ok": True, "link_id": link_id, "channel": channel_slug, "campaign": campaign, "partner": partner}


def log_event(link_id: int, event_type: str, count: int = 1, value: float = 0.0, video_id: int | None = None, notes: str = "") -> dict:
    if event_type not in {"click", "conversion"}:
        raise ValueError("event_type must be 'click' or 'conversion'")
    if count < 1:
        raise ValueError("count must be >= 1")
    ensure_affiliate_tables()
    with get_db() as conn:
        row = conn.execute("SELECT id, channel_id FROM affiliate_links WHERE id = ? AND is_active = 1", (link_id,)).fetchone()
        if not row:
            raise ValueError(f"Active link not found: {link_id}")
        conn.execute(
            """
            INSERT INTO affiliate_events (link_id, channel_id, event_type, video_id, event_value, event_count, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (link_id, row["channel_id"], event_type, video_id, value, count, notes),
        )
    return {"ok": True, "link_id": link_id, "event_type": event_type, "count": count, "value": value}


def report(channel_slug: str | None = None) -> dict:
    ensure_affiliate_tables()
    channel = get_channel(channel_slug) if channel_slug else None
    if channel_slug and not channel:
        raise ValueError(f"Unknown channel: {channel_slug}")
    with get_db() as conn:
        params: list = []
        where = ""
        if channel:
            where = "WHERE l.channel_id = ?"
            params.append(channel["id"])
        rows = conn.execute(
            f"""
            SELECT c.channel_id,
                   l.id as link_id,
                   l.partner_name,
                   l.campaign_name,
                   l.tracking_code,
                   SUM(CASE WHEN e.event_type='click' THEN e.event_count ELSE 0 END) as clicks,
                   SUM(CASE WHEN e.event_type='conversion' THEN e.event_count ELSE 0 END) as conversions,
                   SUM(CASE WHEN e.event_type='conversion' THEN e.event_value ELSE 0 END) as conversion_value
            FROM affiliate_links l
            JOIN channels c ON c.id = l.channel_id
            LEFT JOIN affiliate_events e ON e.link_id = l.id
            {where}
            GROUP BY c.channel_id, l.id
            ORDER BY conversion_value DESC, conversions DESC, clicks DESC
            """,
            params,
        ).fetchall()

    output = []
    for row in rows:
        clicks = int(row["clicks"] or 0)
        conversions = int(row["conversions"] or 0)
        output.append(
            {
                "channel_id": row["channel_id"],
                "link_id": row["link_id"],
                "partner_name": row["partner_name"],
                "campaign_name": row["campaign_name"],
                "tracking_code": row["tracking_code"],
                "clicks": clicks,
                "conversions": conversions,
                "conversion_rate": round((conversions / clicks) * 100, 2) if clicks else 0.0,
                "conversion_value": round(float(row["conversion_value"] or 0.0), 2),
            }
        )
    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "channel_filter": channel_slug or "all",
        "results": output,
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Affiliate tracking in project SQLite (links, clicks, conversions).")
    sub = parser.add_subparsers(dest="command", required=True)

    cmd_init = sub.add_parser("init", help="Create missing affiliate tables/indexes")
    cmd_init.set_defaults(action="init")

    cmd_add = sub.add_parser("add-link", help="Create an affiliate link record")
    cmd_add.add_argument("--channel", required=True)
    cmd_add.add_argument("--campaign", required=True)
    cmd_add.add_argument("--partner", required=True)
    cmd_add.add_argument("--url", required=True)
    cmd_add.add_argument("--tracking-code", required=True)

    cmd_click = sub.add_parser("log-click", help="Log one or more clicks for a link")
    cmd_click.add_argument("--link-id", type=int, required=True)
    cmd_click.add_argument("--count", type=int, default=1)
    cmd_click.add_argument("--video-id", type=int)
    cmd_click.add_argument("--notes", default="")

    cmd_conv = sub.add_parser("log-conversion", help="Log one or more conversions for a link")
    cmd_conv.add_argument("--link-id", type=int, required=True)
    cmd_conv.add_argument("--count", type=int, default=1)
    cmd_conv.add_argument("--value", type=float, default=0.0, help="Total monetary value for this event insertion")
    cmd_conv.add_argument("--video-id", type=int)
    cmd_conv.add_argument("--notes", default="")

    cmd_report = sub.add_parser("report", help="Show attribution report by channel/link")
    cmd_report.add_argument("--channel", help="Optional channel filter")

    args = parser.parse_args()
    try:
        if args.command == "init":
            ensure_affiliate_tables()
            payload = {"ok": True, "message": "affiliate tables ready"}
        elif args.command == "add-link":
            payload = add_link(args.channel, args.campaign, args.partner, args.url, args.tracking_code)
        elif args.command == "log-click":
            payload = log_event(args.link_id, "click", count=args.count, video_id=args.video_id, notes=args.notes)
        elif args.command == "log-conversion":
            payload = log_event(
                args.link_id,
                "conversion",
                count=args.count,
                value=args.value,
                video_id=args.video_id,
                notes=args.notes,
            )
        elif args.command == "report":
            payload = report(args.channel)
        else:
            raise ValueError(f"Unsupported command: {args.command}")
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"affiliate_tracker failed: {exc}",
                    "usage_examples": [
                        "python -m marketing_automation.affiliate_tracker init",
                        "python -m marketing_automation.affiliate_tracker add-link --channel impacto-mundial --campaign q2-launch --partner Semrush --url https://example.com --tracking-code imp-q2-01",
                        "python -m marketing_automation.affiliate_tracker log-click --link-id 1 --count 12",
                        "python -m marketing_automation.affiliate_tracker log-conversion --link-id 1 --count 2 --value 98.0",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

