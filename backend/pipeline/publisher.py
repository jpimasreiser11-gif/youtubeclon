"""
YouTube Automation Pro — Publisher
Uploads videos to YouTube with resumable uploads, thumbnail setting,
and scheduled publishing.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from ..config import env
from ..database import log_api_usage, log_pipeline_step

logger = logging.getLogger("publisher")


def publish_video(video_path: Path, thumbnail_path: Path,
                  metadata: dict, channel: dict) -> str:
    """
    Upload video to YouTube with all metadata.
    Returns the YouTube URL.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

    # Get credentials
    token_file = channel.get("oauth_token_file") or env("YOUTUBE_TOKEN_FILE", ".youtube_token.json")
    secrets_file = channel.get("oauth_client_file") or env("YOUTUBE_CLIENT_SECRETS_FILE")

    if not secrets_file or not Path(secrets_file).exists():
        raise FileNotFoundError(f"OAuth client secrets file not found: {secrets_file}")

    token_path = Path(token_file)
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_info(
            json.loads(token_path.read_text(encoding="utf-8")), SCOPES
        )

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets_file), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    youtube = build("youtube", "v3", credentials=creds)

    # Upload video with resumable upload
    title = metadata.get("title", "Untitled Video")[:100]
    description = metadata.get("description", "")[:5000]
    tags = [t.strip() for t in metadata.get("tags", "").split(",") if t.strip()][:20]
    category_id = metadata.get("category_id", "27")
    privacy = metadata.get("privacy_status", "public")

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags,
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    logger.info(f"📤 Uploading: {title}")
    logger.info(f"   File: {video_path} ({video_path.stat().st_size / 1024 / 1024:.0f}MB)")

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(
            str(video_path),
            chunksize=10 * 1024 * 1024,  # 10MB chunks
            resumable=True,
        ),
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            logger.info(f"   Upload progress: {int(status.progress() * 100)}%")

    video_id = response["id"]
    youtube_url = f"https://www.youtube.com/watch?v={video_id}"

    # Set thumbnail
    if thumbnail_path.exists():
        try:
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path)),
            ).execute()
            logger.info("   ✅ Thumbnail set")
        except Exception as exc:
            logger.warning(f"   ⚠️ Thumbnail set failed: {exc}")

    log_api_usage("youtube_data_api", "videos.insert", requests=1)
    logger.info(f"   ✅ Published: {youtube_url}")

    return youtube_url
