from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from backend.database import get_all_channels, get_channel, init_db

SPONSOR_DIRECTORY: dict[str, list[dict[str, str]]] = {
    "impacto-mundial": [
        {"name": "Semrush", "contact": "https://www.semrush.com/lp/affiliate-program/en/", "angle": "SEO intelligence for investigative creators"},
        {"name": "Surfshark", "contact": "https://surfshark.com/affiliate-signup", "angle": "Privacy/safety sponsor fit for geopolitics narratives"},
        {"name": "Kinsta", "contact": "https://affiliate.kinsta.com/register", "angle": "High-ticket hosting for content hubs and newsletters"},
    ],
    "mentes-rotas": [
        {"name": "Systeme.io", "contact": "https://www.systeme.io/affiliate-program", "angle": "Recurring offer for true-crime education funnels"},
        {"name": "Moosend", "contact": "https://www.moosend.com/affiliate-program/", "angle": "Email lifecycle monetization for mystery audiences"},
        {"name": "Notta", "contact": "https://www.notta.ai/en/affiliate", "angle": "Transcription workflows for case breakdown production"},
    ],
    "el-loco-de-la-ia": [
        {"name": "HubSpot", "contact": "affiliates@hubspot.com", "angle": "B2B automation partner for AI tutorials"},
        {"name": "Elementor", "contact": "https://elementor.com/affiliates/", "angle": "No-code sites for AI-powered side projects"},
        {"name": "Semrush", "contact": "https://www.semrush.com/lp/affiliate-program/en/", "angle": "SEO stack for AI growth content"},
    ],
    "mind-warp": [
        {"name": "Kinsta", "contact": "https://affiliate.kinsta.com/register", "angle": "Premium infrastructure for knowledge businesses"},
        {"name": "Notta", "contact": "https://www.notta.ai/en/affiliate", "angle": "Learning/transcript workflows for psychology education"},
        {"name": "HubSpot", "contact": "affiliates@hubspot.com", "angle": "CRM for behavioral newsletter growth loops"},
    ],
    "wealth-files": [
        {"name": "Semrush", "contact": "https://www.semrush.com/lp/affiliate-program/en/", "angle": "Research and positioning for finance creators"},
        {"name": "Systeme.io", "contact": "https://www.systeme.io/affiliate-program", "angle": "Recurring funnels for wealth playbooks"},
        {"name": "Kinsta", "contact": "https://affiliate.kinsta.com/register", "angle": "High-ticket business stack sponsor"},
    ],
    "dark-science": [
        {"name": "Surfshark", "contact": "https://surfshark.com/affiliate-signup", "angle": "Security angle for science/tech audience"},
        {"name": "Hostinger", "contact": "https://www.hostinger.com/affiliates", "angle": "Accessible hosting partner for STEM projects"},
        {"name": "Kinsta", "contact": "https://affiliate.kinsta.com/register", "angle": "Premium engineering-focused sponsor"},
    ],
}


def _build_subject(channel_name: str, sponsor_name: str, niche: str) -> str:
    return f"Partnership opportunity: {channel_name} x {sponsor_name} ({niche})"


def _build_email_body(channel: dict, sponsor: dict[str, str], recent_topics: list[str]) -> str:
    topics_line = ", ".join(recent_topics[:3]) if recent_topics else channel.get("niche", "")
    return (
        f"Hi {sponsor['name']} team,\n\n"
        f"My name is {{YOUR_NAME}} and I run {channel.get('name', channel['channel_id'])}, a "
        f"{channel.get('language', 'es')}-language YouTube channel focused on {channel.get('niche', 'education')}.\n\n"
        f"We are publishing consistently ({channel.get('frequency', '4/week')}) and recent audience pull topics include: {topics_line}.\n"
        f"I believe there is a strong fit with {sponsor['name']} because {sponsor['angle']}.\n\n"
        "Proposed collaboration:\n"
        "- 1 integrated mention in a high-intent video\n"
        "- 1 pinned comment + description CTA\n"
        "- Performance recap after 7 days (views, CTR proxy, clicks)\n\n"
        "If useful, I can send a media snapshot and draft integration concept this week.\n\n"
        "Best,\n"
        "{YOUR_NAME}\n"
        "{YOUR_EMAIL}\n"
    )


def _recent_topic_snippets(channel: dict) -> list[str]:
    raw = channel.get("seed_topics", "[]")
    try:
        loaded = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(loaded, list):
            return [str(x) for x in loaded if str(x).strip()]
    except Exception:
        pass
    return []


def generate_outreach(channel_id: str | None = None) -> dict:
    init_db()
    channels = [get_channel(channel_id)] if channel_id else get_all_channels()
    channels = [c for c in channels if c]
    if not channels:
        raise ValueError("No channels found. Use a valid --channel or initialize DB.")

    generated: list[dict] = []
    for channel in channels:
        sponsors = SPONSOR_DIRECTORY.get(channel["channel_id"], [])
        if not sponsors:
            continue
        topics = _recent_topic_snippets(channel)
        drafts = []
        for sponsor in sponsors:
            drafts.append(
                {
                    "sponsor": sponsor["name"],
                    "contact": sponsor["contact"],
                    "subject": _build_subject(channel.get("name", channel["channel_id"]), sponsor["name"], channel.get("niche", "")),
                    "body": _build_email_body(channel, sponsor, topics),
                }
            )
        generated.append(
            {
                "channel_id": channel["channel_id"],
                "channel_name": channel.get("name", channel["channel_id"]),
                "niche": channel.get("niche", ""),
                "draft_count": len(drafts),
                "drafts": drafts,
            }
        )

    return {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "channel_count": len(generated),
        "results": generated,
    }


def _cli() -> int:
    parser = argparse.ArgumentParser(
        description="Generate sponsor outreach templates per channel using project sponsor/contact data."
    )
    parser.add_argument("--channel", help="Channel slug (default: all 6 channels)")
    parser.add_argument("--compact", action="store_true", help="Print compact JSON")
    args = parser.parse_args()
    try:
        payload = generate_outreach(channel_id=args.channel)
    except Exception as exc:
        print(
            json.dumps(
                {"ok": False, "error": f"email_outreach failed: {exc}", "hint": "Try: python -m marketing_automation.email_outreach --channel impacto-mundial"},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())

