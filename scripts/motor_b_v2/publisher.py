import os
from typing import Dict, Any, List


def upload_to_youtube(
    video_path: str,
    title: str,
    description_hook: str,
    tags: List[str],
    category_id: str = "27",
) -> Dict[str, Any]:
    """Best-effort uploader.

    If YouTube credentials are not configured, returns a dry result instead of failing.
    """
    token_file = "youtube_token.json"
    if not os.path.exists(token_file):
        return {
            "video_id": "dry-run",
            "url": "",
            "title": title,
            "published": False,
            "reason": "youtube_token.json not found",
        }

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        import google.oauth2.credentials

        creds = google.oauth2.credentials.Credentials.from_authorized_user_file(
            token_file,
            [
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube.readonly",
            ],
        )
        yt = build("youtube", "v3", credentials=creds)

        description = (
            f"{description_hook}\n\n"
            "Want deeper mystery breakdowns?\n"
            "- Audible trial: [AFFILIATE_LINK]\n"
            "- Mystery books: [AFFILIATE_LINK]\n\n"
            f"Tags: {', '.join(tags[:15])}\n"
            "#mystery #unsolved #paranormal #history"
        )

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:30],
                "categoryId": category_id,
                "defaultLanguage": "en",
                "defaultAudioLanguage": "en",
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
                "madeForKids": False,
            },
        }

        media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=10 * 1024 * 1024)
        req = yt.videos().insert(part=",".join(body.keys()), body=body, media_body=media)

        response = None
        while response is None:
            _, response = req.next_chunk()

        vid = response["id"]
        return {"video_id": vid, "url": f"https://youtube.com/shorts/{vid}", "title": title, "published": True}
    except Exception as e:
        return {
            "video_id": "error",
            "url": "",
            "title": title,
            "published": False,
            "reason": str(e),
        }
