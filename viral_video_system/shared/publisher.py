import os


def upload_to_youtube(video_path, title, description, tags, dry_run=True, credentials_data=None):
    if dry_run:
        return {"platform": "youtube", "video_id": "dryrun_yt_001", "url": "https://youtube.com/shorts/dryrun_yt_001"}

    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials

    if credentials_data:
        credentials = Credentials(
            token=credentials_data.get("access_token"),
            refresh_token=credentials_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=credentials_data.get("client_id"),
            client_secret=credentials_data.get("client_secret"),
            scopes=["https://www.googleapis.com/auth/youtube.upload"],
        )
    else:
        credentials = Credentials.from_authorized_user_file(
            "token.json", ["https://www.googleapis.com/auth/youtube.upload"]
        )
    youtube = build("youtube", "v3", credentials=credentials)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description,
            "tags": tags,
            "categoryId": "22",
            "defaultLanguage": "es",
        },
        "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False, "madeForKids": False},
    }

    media = MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=1024 * 1024 * 10)
    request = youtube.videos().insert(part=",".join(body.keys()), body=body, media_body=media)
    response = None
    while response is None:
        _, response = request.next_chunk()
    vid = response["id"]
    return {"platform": "youtube", "video_id": vid, "url": f"https://youtube.com/shorts/{vid}"}
