import os


def find_and_download_source(topic, output_dir="./viral_video_system/temp", dry_run=True):
    os.makedirs(output_dir, exist_ok=True)

    if dry_run:
        return {
            "id": "mock-source-1",
            "title": f"Fuente mock para {topic}",
            "filepath": os.path.join(output_dir, "source_mock.mp4"),
            "license": "CC-BY",
            "url": "mock://source/video",
        }

    try:
        import yt_dlp
    except Exception as e:
        raise RuntimeError(f"yt-dlp no disponible para Motor A real: {e}")

    ydl_opts = {
        "format": "bestvideo[height<=1080]+bestaudio/best",
        "outtmpl": f"{output_dir}/source_%(id)s.%(ext)s",
        "quiet": True,
        "max_downloads": 1,
    }

    query = f"ytsearch1:{topic} podcast entrevista -shorts"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(query, download=True)
        entry = result["entries"][0]
        return {
            "id": entry.get("id"),
            "title": entry.get("title"),
            "filepath": ydl.prepare_filename(entry),
            "license": entry.get("license", "unknown"),
            "url": entry.get("webpage_url"),
        }
