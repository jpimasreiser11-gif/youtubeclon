"""
YouTube Automation Pro — Orchestrator
Coordinates the entire video generation pipeline for each channel.
Handles retry logic, quota management, parallel execution, and comprehensive metrics.
"""
from __future__ import annotations

import json
import logging
import time
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from ..config import env, env_int, PIPELINE_CONFIG, LOGGING_CONFIG
from ..database import (
    get_all_channels, get_channel, get_trends,
    create_video, update_video, log_pipeline_step,
    mark_trend_used,
)
from .trend_finder import find_trending_topics
from .script_writer import generate_script
from .voice_generator import generate_voice
from .video_builder import build_video, download_broll
from .thumbnail_creator import create_thumbnails
from .metadata_writer import generate_metadata

logger = logging.getLogger("orchestrator")


def run_single_channel(channel_id: str, topic: str | None = None,
                       upload: bool = False) -> dict:
    """
    Run the complete pipeline for a single channel.

    Steps:
    1. Find trending topic (or use provided topic)
    2. Generate script
    3. Generate voice audio
    4. Download B-roll
    5. Create thumbnail
    6. Build video
    7. Generate metadata
    8. (Optional) Upload to YouTube
    """
    channel = get_channel(channel_id)
    if not channel:
        raise ValueError(f"Channel not found: {channel_id}")

    channel_name = channel["name"]
    start_time = time.time()
    phase_times = {}  # Track time per phase
    result = {
        "channel_id": channel_id,
        "channel_name": channel_name,
        "status": "running",
        "steps": {},
        "phase_times": phase_times,
        "error": None,
        "video_id": None,
    }

    max_retries = PIPELINE_CONFIG["max_retries"]

    logger.info(f"{'='*60}")
    logger.info(f"🚀 Starting pipeline for '{channel_name}' ({channel_id})")
    logger.info(f"{'='*60}")

    for attempt in range(1, max_retries + 1):
        try:
            if attempt > 1:
                logger.info(f"🔄 Retry {attempt}/{max_retries} for '{channel_name}'")

            # ── Step 1: Get topic ────────────────────────────
            phase_start = time.time()
            if not topic:
                logger.info("📡 Step 1: Finding trending topic...")
                try:
                    trends = find_trending_topics(channel)
                    if trends:
                        topic = trends[0]["topic"]
                        mark_trend_used(trends[0].get("id", 0))
                        logger.info(f"   Trending topic: {topic}")
                    else:
                        # Fallback to seed topics
                        seed_topics = json.loads(channel.get("seed_topics", "[]"))
                        topic = seed_topics[0] if seed_topics else f"{channel.get('niche', 'topic')} guide"
                        logger.info(f"   Using seed topic: {topic}")
                except Exception as exc:
                    logger.warning(f"   Trend finding failed: {exc}. Using seed topic.")
                    seed_topics = json.loads(channel.get("seed_topics", "[]"))
                    topic = seed_topics[0] if seed_topics else channel.get("niche", "topic")

            result["steps"]["trends"] = "ok"
            phase_times["trends"] = round(time.time() - phase_start, 1)
            result["topic"] = topic

            # ── Create video record ──────────────────────────
            video_id = create_video(channel["id"], topic)
            result["video_id"] = video_id

            # ── Step 2: Generate script ──────────────────────
            phase_start = time.time()
            logger.info("📝 Step 2: Generating script...")
            script_result = generate_script(topic, channel, video_id=video_id)
            result["steps"]["script"] = "ok"
            phase_times["script"] = round(time.time() - phase_start, 1)
            result["title"] = script_result["title"]

            # ── Step 3: Generate voice ───────────────────────
            phase_start = time.time()
            logger.info("🔊 Step 3: Generating voice...")
            audio_path = generate_voice(
                script_result["script"], channel, video_id=video_id
            )
            result["steps"]["voice"] = "ok"
            phase_times["voice"] = round(time.time() - phase_start, 1)

            # ── Step 4: Download B-roll ──────────────────────
            phase_start = time.time()
            logger.info("📹 Step 4: Downloading B-roll...")
            broll_markers = script_result.get("broll_markers", [])
            word_count = int(script_result.get("word_count", 0) or 0)
            est_minutes = max(4.0, min(18.0, word_count / 150.0 if word_count else 8.0))
            min_clips = max(12, min(28, int(est_minutes * 2.0) + 4))
            clips = download_broll(
                broll_markers,
                channel,
                min_clips=min_clips,
                topic=topic or "",
                script_text=script_result.get("script", ""),
            )
            result["steps"]["broll"] = "ok"
            phase_times["broll"] = round(time.time() - phase_start, 1)

            # ── Step 5: Create thumbnail ─────────────────────
            phase_start = time.time()
            logger.info("🖼️  Step 5: Creating thumbnail...")
            thumbnail_path = create_thumbnails(
                script_result["title"], channel, video_id=video_id
            )
            result["steps"]["thumbnail"] = "ok"
            phase_times["thumbnail"] = round(time.time() - phase_start, 1)

            # ── Step 6: Build video ──────────────────────────
            phase_start = time.time()
            logger.info("🎬 Step 6: Building video...")
            video_path = build_video(
                audio_path, script_result["script"],
                thumbnail_path, clips, channel, video_id=video_id
            )
            result["steps"]["video"] = "ok"
            phase_times["video"] = round(time.time() - phase_start, 1)

            # ── Step 7: Generate metadata ────────────────────
            phase_start = time.time()
            logger.info("📋 Step 7: Generating metadata...")
            metadata = generate_metadata(
                script_result["title"], script_result["script"],
                channel, video_id=video_id
            )
            result["steps"]["metadata"] = "ok"
            phase_times["metadata"] = round(time.time() - phase_start, 1)

            # ── Step 7.5: Quality gate before upload ───────────
            phase_start = time.time()
            logger.info("✅ Step 7.5: Running quality gate...")
            try:
                from pipeline.quality_control import run_quality_checks
                qc = run_quality_checks(
                    video_path=video_path,
                    metadata=metadata,
                    thumbnail_path=thumbnail_path,
                    subtitles_path=None,  # subtitles may be burned into final video
                )
                result["quality"] = qc
                if not qc.get("ok"):
                    result["steps"]["quality_gate"] = "error"
                    update_video(video_id, {"status": "needs_review"})
                    log_pipeline_step(
                        channel["id"], video_id, "quality_gate", "error",
                        f"Quality gate failed: {qc.get('checks', [])}",
                    )
                    result["status"] = "needs_review"
                    result["error"] = "Quality gate failed"
                    phase_times["quality_gate"] = round(time.time() - phase_start, 1)
                    return result
                result["steps"]["quality_gate"] = "ok"
                log_pipeline_step(channel["id"], video_id, "quality_gate", "ok", "Quality gate passed")
                phase_times["quality_gate"] = round(time.time() - phase_start, 1)
            except Exception as exc:
                logger.warning(f"   Quality gate unavailable/error: {exc}")
                result["steps"]["quality_gate"] = "skipped"
                phase_times["quality_gate"] = round(time.time() - phase_start, 1)

            # ── Step 8: Upload (if requested) ────────────────
            if upload:
                phase_start = time.time()
                logger.info("📤 Step 8: Uploading to YouTube...")
                try:
                    from .publisher import publish_video
                    youtube_url = publish_video(
                        video_path, thumbnail_path, metadata, channel
                    )
                    update_video(video_id, {
                        "youtube_url": youtube_url,
                        "status": "published",
                        "published_at": datetime.now().isoformat(),
                    })
                    result["steps"]["upload"] = "ok"
                    phase_times["upload"] = round(time.time() - phase_start, 1)
                    result["youtube_url"] = youtube_url
                except Exception as exc:
                    logger.error(f"   Upload failed: {exc}")
                    result["steps"]["upload"] = "error"
                    phase_times["upload"] = round(time.time() - phase_start, 1)
                    update_video(video_id, {"status": "ready"})
            else:
                result["steps"]["upload"] = "skipped"
                update_video(video_id, {"status": "ready"})

            # ── Success ──────────────────────────────────────
            result["status"] = "ok"
            elapsed = time.time() - start_time
            result["elapsed_seconds"] = round(elapsed, 1)

            log_pipeline_step(channel["id"], video_id, "pipeline_complete", "ok",
                              f"Pipeline completed in {elapsed:.0f}s")

            logger.info(f"{'='*60}")
            logger.info(f"✅ Pipeline complete for '{channel_name}' in {elapsed:.0f}s")
            logger.info(f"{'='*60}")

            return result

        except Exception as exc:
            error_msg = f"{exc}\n{traceback.format_exc()}"
            logger.error(f"❌ Pipeline error (attempt {attempt}): {exc}")
            result["error"] = str(exc)

            if result.get("video_id"):
                update_video(result["video_id"], {
                    "status": "error",
                    "error_message": error_msg[:1000],
                })
                log_pipeline_step(channel["id"], result["video_id"],
                                  "pipeline_error", "error", str(exc)[:500])

            if attempt >= max_retries:
                result["status"] = "error"
                return result

            # Backoff before retry
            wait = min(30, 5 * attempt)
            logger.info(f"   Waiting {wait}s before retry...")
            time.sleep(wait)
            topic = None  # Reset topic for fresh attempt

    return result


def run_daily_pipeline(channels: list[str] | None = None,
                       upload: bool = False) -> list[dict]:
    """
    Run the pipeline for multiple channels in parallel.
    If no channels specified, runs all active channels.
    """
    if channels:
        channel_list = [get_channel(cid) for cid in channels]
        channel_list = [c for c in channel_list if c]
    else:
        channel_list = [c for c in get_all_channels() if c.get("is_active")]

    if not channel_list:
        logger.warning("No active channels to process")
        return []

    logger.info(f"🌐 Starting daily pipeline for {len(channel_list)} channels")

    max_workers = min(3, len(channel_list))  # Max 3 parallel
    results: list[dict] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_single_channel, ch["channel_id"], upload=upload): ch
            for ch in channel_list
        }

        for future in as_completed(futures):
            channel = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                logger.error(f"Channel '{channel['name']}' failed: {exc}")
                results.append({
                    "channel_id": channel["channel_id"],
                    "status": "error",
                    "error": str(exc),
                })

    # Generate comprehensive summary
    summary = _generate_pipeline_summary(results)
    
    ok_count = sum(1 for r in results if r["status"] == "ok")
    err_count = len(results) - ok_count
    logger.info(f"🏁 Daily pipeline complete: {ok_count} ok, {err_count} errors")
    logger.info(f"📊 Summary: {json.dumps(summary, indent=2)}")

    return results


def _generate_pipeline_summary(results: list[dict]) -> dict:
    """Generate comprehensive metrics summary for a pipeline run."""
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total_channels": len(results),
        "statuses": defaultdict(int),
        "phase_metrics": defaultdict(lambda: {"ok": 0, "error": 0, "skipped": 0}),
        "total_elapsed_seconds": 0.0,
        "channels": [],
    }

    for result in results:
        status = result.get("status", "unknown")
        summary["statuses"][status] += 1
        summary["total_elapsed_seconds"] += result.get("elapsed_seconds", 0)

        channel_summary = {
            "channel_id": result.get("channel_id"),
            "status": status,
            "elapsed_seconds": result.get("elapsed_seconds", 0),
            "topic": result.get("topic", ""),
            "title": result.get("title", ""),
            "video_id": result.get("video_id"),
        }

        # Aggregate phase metrics
        for phase, phase_status in result.get("steps", {}).items():
            if phase_status == "ok":
                summary["phase_metrics"][phase]["ok"] += 1
            elif phase_status == "error":
                summary["phase_metrics"][phase]["error"] += 1
                channel_summary["phase_error"] = phase
            elif phase_status == "skipped":
                summary["phase_metrics"][phase]["skipped"] += 1

        if result.get("error"):
            channel_summary["error"] = result["error"]

        summary["channels"].append(channel_summary)

    # Convert defaultdict to regular dict for JSON serialization
    summary["statuses"] = dict(summary["statuses"])
    summary["phase_metrics"] = {k: dict(v) for k, v in summary["phase_metrics"].items()}

    return summary


def save_pipeline_report(results: list[dict], output_dir: Path | None = None) -> Path:
    """Save detailed pipeline report to JSON and HTML."""
    if output_dir is None:
        output_dir = Path("logs")
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary = _generate_pipeline_summary(results)

    # Save JSON report
    json_path = output_dir / f"pipeline_report_{timestamp}.json"
    json_path.write_text(json.dumps(summary, indent=2, default=str))
    logger.info(f"📄 Pipeline report saved: {json_path}")

    # Save human-readable summary
    txt_path = output_dir / f"pipeline_summary_{timestamp}.txt"
    txt_lines = [
        "=" * 70,
        f"PIPELINE EXECUTION SUMMARY — {summary['timestamp']}",
        "=" * 70,
        f"Total Channels: {summary['total_channels']}",
        f"Status Breakdown: {summary['statuses']}",
        f"Total Time: {summary['total_elapsed_seconds']:.1f}s",
        "",
        "PHASE METRICS:",
    ]

    for phase, metrics in summary["phase_metrics"].items():
        txt_lines.append(f"  {phase}: ok={metrics['ok']}, error={metrics['error']}, skipped={metrics['skipped']}")

    txt_lines.append("")
    txt_lines.append("CHANNEL DETAILS:")
    for ch in summary["channels"]:
        txt_lines.append(f"  {ch['channel_id']}: {ch['status']} ({ch['elapsed_seconds']:.1f}s)")
        if ch.get("title"):
            txt_lines.append(f"    Title: {ch['title']}")
        if ch.get("phase_error"):
            txt_lines.append(f"    Failed Phase: {ch['phase_error']}")
        if ch.get("error"):
            txt_lines.append(f"    Error: {ch['error']}")

    txt_path.write_text("\n".join(txt_lines))
    logger.info(f"📋 Pipeline summary saved: {txt_path}")

    return json_path
