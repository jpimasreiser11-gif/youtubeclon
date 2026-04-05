#!/usr/bin/env python3
"""
Bridge runner for gradual migration to viral_video_system.

Behavior:
- Always accepts same CLI contract as ingest.py
- If enabled, executes new pipeline first (best effort)
- Delegates to current ingest.py unless VIRAL_BRIDGE_ONLY=1
"""

import argparse
import os
import subprocess
import sys
import json
import base64
import shutil
import uuid
import tempfile
from pathlib import Path

import psycopg2


def _is_true(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _get_db_config():
    return {
        "user": os.getenv("POSTGRES_USER", "n8n"),
        "password": os.getenv("POSTGRES_PASSWORD", "n8n"),
        "host": os.getenv("POSTGRES_HOST", "127.0.0.1"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "database": os.getenv("POSTGRES_DB", "antigravity"),
    }


def _register_viral_output(project_id: str, result_json_path: Path, root_dir: Path) -> bool:
    if not result_json_path.exists():
        return False

    with open(result_json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    artifacts = payload.get("artifacts") or {}
    final_video = artifacts.get("final_video")
    if not final_video or not os.path.exists(final_video):
        return False

    storage_base = root_dir / "app" / "storage"
    clips_dir = storage_base / "clips"
    processed_dir = storage_base / "processed"
    thumbs_dir = storage_base / "thumbnails"
    clips_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir.mkdir(parents=True, exist_ok=True)

    clip_id = str(uuid.uuid4())
    final_clip_path = clips_dir / f"{clip_id}.mp4"
    processed_clip_path = processed_dir / f"{clip_id}.mp4"
    thumb_path = thumbs_dir / f"{clip_id}.jpg"

    shutil.copy2(final_video, final_clip_path)
    shutil.copy2(final_video, processed_clip_path)

    ffmpeg_bin = os.getenv("FFMPEG_EXE", "ffmpeg")
    subprocess.run([
        ffmpeg_bin,
        "-y",
        "-i",
        str(final_clip_path),
        "-ss",
        "00:00:01",
        "-vframes",
        "1",
        str(thumb_path),
    ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    analysis = payload.get("analysis") or {}
    script_payload = artifacts.get("script") or {}
    transcript_text = "\n".join([
        script_payload.get("parte_1", ""),
        script_payload.get("parte_2", ""),
        script_payload.get("parte_3", ""),
    ]).strip()

    conn = psycopg2.connect(**_get_db_config())
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'clips'
            """
        )
        clip_columns = {row[0] for row in cur.fetchall()}
        has_extended_clip_cols = all(
            c in clip_columns
            for c in ("title_generated", "description_generated", "hook_description", "payoff_description")
        )

        if has_extended_clip_cols:
            cur.execute(
                """
                INSERT INTO clips (
                    project_id, start_time, end_time, virality_score, transcript_json,
                    title_generated, description_generated, hook_description, payoff_description
                ) VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    project_id,
                    0.0,
                    60.0,
                    88,
                    json.dumps([{"text": transcript_text}]),
                    analysis.get("hook_numero_1", "Viral clip"),
                    analysis.get("angulo_unico", ""),
                    analysis.get("hook_numero_1", ""),
                    analysis.get("hook_numero_2", ""),
                ),
            )
        else:
            cur.execute(
                """
                INSERT INTO clips (
                    project_id, start_time, end_time, virality_score, transcript_json
                ) VALUES (%s::uuid, %s, %s, %s, %s)
                RETURNING id;
                """,
                (
                    project_id,
                    0.0,
                    60.0,
                    88,
                    json.dumps([{"text": transcript_text}]),
                ),
            )
        new_clip_id = str(cur.fetchone()[0])

        # Ensure the DB clip id matches file names expected by UI endpoints
        db_clip_path = clips_dir / f"{new_clip_id}.mp4"
        db_processed_path = processed_dir / f"{new_clip_id}.mp4"
        db_thumb_path = thumbs_dir / f"{new_clip_id}.jpg"

        if final_clip_path.exists():
            final_clip_path.replace(db_clip_path)
        if processed_clip_path.exists():
            processed_clip_path.replace(db_processed_path)
        if thumb_path.exists():
            thumb_path.replace(db_thumb_path)

        cur.execute(
            "INSERT INTO video_versions (clip_id, version, file_path) VALUES (%s, 'preview', %s)",
            (new_clip_id, str(db_clip_path)),
        )
        cur.execute(
            "INSERT INTO thumbnails (clip_id, url) VALUES (%s, %s)",
            (new_clip_id, str(db_thumb_path)),
        )

        cur.execute(
            "UPDATE projects SET project_status = 'COMPLETED', updated_at = NOW() WHERE id = %s::uuid",
            (project_id,),
        )

        conn.commit()
        return True
    except Exception as exc:
        conn.rollback()
        print(f"[bridge] Failed to register viral output in DB: {exc}")
        return False
    finally:
        conn.close()


def _get_project_youtube_credentials(project_id: str):
    conn = psycopg2.connect(**_get_db_config())
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT pc.credentials_data
            FROM projects p
            JOIN platform_credentials pc ON pc.user_id = p.user_id
            WHERE p.id = %s::uuid
              AND pc.platform = 'youtube'
              AND pc.is_active = true
            LIMIT 1;
            """,
            (project_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None
    except Exception as exc:
        print(f"[bridge] Failed to read YouTube credentials from DB: {exc}")
        return None
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_id", help="UUID of the project")
    parser.add_argument("url", help="Video source URL")
    parser.add_argument("--pipeline-mode", default="auto", choices=["auto", "motor_a", "motor_b"])
    parser.add_argument("--pipeline-niche", default="finanzas personales")
    parser.add_argument("--pipeline-dry-run", default="1")
    parser.add_argument("--pipeline-input-b64", default="")
    parser.add_argument("--pipeline-trend-mode", default="internet", choices=["internet", "manual-only"])
    parser.add_argument("--audio-pro", dest="audio_pro", action="store_true")
    parser.add_argument("--no-audio-pro", dest="audio_pro", action="store_false")
    parser.add_argument("--smart-reframe", dest="smart_reframe", action="store_true")
    parser.add_argument("--no-smart-reframe", dest="smart_reframe", action="store_false")
    parser.add_argument("--clean-speech", dest="clean_speech", action="store_true")
    parser.add_argument("--no-clean-speech", dest="clean_speech", action="store_false")
    parser.add_argument("--b-roll", dest="b_roll", action="store_true")
    parser.add_argument("--no-b-roll", dest="b_roll", action="store_false")
    parser.set_defaults(audio_pro=True, smart_reframe=True, clean_speech=True, b_roll=True)
    args = parser.parse_args()
    is_from_scratch_motor_b = str(args.url or "").startswith("motorb://from-scratch/")

    root_dir = Path(__file__).resolve().parents[2]
    py_exec = sys.executable

    # Step 1: run new architecture in best-effort mode
    use_new = _is_true(os.getenv("USE_VIRAL_SYSTEM", "0")) or args.pipeline_mode in {"motor_a", "motor_b"} or is_from_scratch_motor_b
    use_legacy_ingest = not is_from_scratch_motor_b
    if use_new:
        niche = args.pipeline_niche or os.getenv("VIRAL_NICHE", "finanzas personales")
        mode = args.pipeline_mode or os.getenv("VIRAL_PIPELINE_MODE", "auto")
        dry_run = _is_true(args.pipeline_dry_run or os.getenv("VIRAL_PIPELINE_DRY_RUN", "1"))

        bridge_cmd = [
            py_exec,
            str(root_dir / "scripts" / "run_viral_pipeline.py"),
            "--niche",
            niche,
            "--mode",
            mode,
        ]
        if args.pipeline_trend_mode:
            bridge_cmd.extend(["--trend-mode", args.pipeline_trend_mode])

        if args.pipeline_input_b64:
            try:
                decoded = base64.b64decode(args.pipeline_input_b64).decode("utf-8")
                json.loads(decoded)
                bridge_cmd.extend(["--input-json", decoded])
            except Exception as exc:
                print(f"[bridge] Invalid pipeline input payload, ignoring: {exc}")

        if dry_run:
            bridge_cmd.append("--dry-run")

        creds_temp_file = None
        if not dry_run:
            creds = _get_project_youtube_credentials(args.project_id)
            if creds:
                fd, temp_path = tempfile.mkstemp(prefix="yt_creds_", suffix=".json")
                os.close(fd)
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(creds, f)
                creds_temp_file = temp_path
                bridge_cmd.extend(["--youtube-creds-file", temp_path])
            else:
                print("[bridge] No active YouTube OAuth credentials found for this project user.")

        print(f"[bridge] Running viral pipeline: {' '.join(bridge_cmd)}")
        try:
            result = subprocess.run(bridge_cmd, cwd=str(root_dir), check=False)
            if result.returncode != 0:
                if use_legacy_ingest:
                    print(f"[bridge] Viral pipeline returned {result.returncode}, continuing with legacy ingest.")
                else:
                    print(f"[bridge] Viral pipeline returned {result.returncode}. Legacy ingest disabled for Motor B from scratch.")
                    return result.returncode
            elif not dry_run:
                out_json = root_dir / "output_test" / "viral_system" / "last_run.json"
                persisted = _register_viral_output(args.project_id, out_json, root_dir)
                if persisted:
                    print("[bridge] Viral output persisted in DB. Skipping legacy ingest.")
                    use_legacy_ingest = False
                else:
                    if use_legacy_ingest:
                        print("[bridge] Could not persist viral output. Falling back to legacy ingest.")
                    else:
                        print("[bridge] Could not persist viral output and legacy ingest is disabled for Motor B from scratch.")
                        return 1
        except Exception as exc:
            if use_legacy_ingest:
                print(f"[bridge] Viral pipeline execution failed: {exc}. Continuing with legacy ingest.")
            else:
                print(f"[bridge] Viral pipeline execution failed: {exc}. Legacy ingest disabled for Motor B from scratch.")
                return 1
        finally:
            if creds_temp_file and os.path.exists(creds_temp_file):
                try:
                    os.remove(creds_temp_file)
                except Exception:
                    pass

    # Step 2: optional bridge-only mode for testing
    if _is_true(os.getenv("VIRAL_BRIDGE_ONLY", "0")):
        print("[bridge] VIRAL_BRIDGE_ONLY=1 enabled, skipping legacy ingest.")
        return 0

    if not use_legacy_ingest:
        return 0

    # Step 3: delegate to legacy ingest for full compatibility
    legacy_ingest = Path(__file__).resolve().parent / "ingest.py"
    cmd = [py_exec, str(legacy_ingest), args.project_id, args.url]
    if args.audio_pro:
        cmd.append("--audio-pro")
    if args.smart_reframe:
        cmd.append("--smart-reframe")
    if args.clean_speech:
        cmd.append("--clean-speech")
    if args.b_roll:
        cmd.append("--b-roll")

    print(f"[bridge] Running legacy ingest: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(root_dir), check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
