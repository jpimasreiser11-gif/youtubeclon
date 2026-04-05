import os
import time
import random
import subprocess


def _run(cmd):
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except Exception:
        return False


def _create_motion_background(output_path, duration=8, seed=0):
    # Fully local dynamic background to avoid static "photo + text" look.
    filter_chain = (
        "scale=1080:1920,"
        "format=yuv420p,"
        "eq=saturation=1.35:contrast=1.08:brightness=0.02,"
        "noise=alls=14:allf=t+u,"
        "unsharp=5:5:0.8:3:3:0.2"
    )
    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size=1080x1920:rate=30:duration={max(4, int(duration))}",
        "-vf",
        filter_chain,
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "22",
        "-pix_fmt",
        "yuv420p",
        output_path,
    ]
    return _run(cmd)


def _fetch_pexels_videos(keywords, output_dir, num_assets):
    api_key = os.getenv("PEXELS_API_KEY", "").strip()
    if not api_key:
        return []

    try:
        import requests
    except Exception:
        return []

    assets = []
    headers = {"Authorization": api_key}
    safe_keywords = (keywords or ["business", "money", "growth"])[:num_assets]

    for i, kw in enumerate(safe_keywords):
        try:
            url = f"https://api.pexels.com/videos/search?query={requests.utils.quote(str(kw))}&per_page=5&orientation=portrait"
            resp = requests.get(url, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json() or {}
            videos = data.get("videos") or []
            if not videos:
                continue

            picked = videos[0]
            files = picked.get("video_files") or []
            target = None
            for f in files:
                if int(f.get("width", 0)) >= 720 and int(f.get("height", 0)) >= 1280:
                    target = f
                    break
            if not target and files:
                target = files[0]
            if not target:
                continue

            video_url = target.get("link")
            if not video_url:
                continue

            out_path = os.path.join(output_dir, f"stock_{i}.mp4")
            vresp = requests.get(video_url, timeout=60)
            vresp.raise_for_status()
            with open(out_path, "wb") as f:
                f.write(vresp.content)
            assets.append(out_path)
        except Exception:
            continue

    return assets


def generate_background_media(keywords, output_dir, num_assets=6, dry_run=False, style_profile="default"):
    os.makedirs(output_dir, exist_ok=True)

    mystery_terms = [
        "dark forest fog",
        "abandoned building night",
        "secret laboratory",
        "mysterious alley rain",
        "old archive documents",
        "surveillance camera dark",
    ]

    search_terms = list(keywords or [])
    if style_profile == "mystery":
        search_terms = mystery_terms + search_terms

    stock = [] if dry_run else _fetch_pexels_videos(search_terms, output_dir, num_assets)
    assets = []

    for idx, item in enumerate(stock):
        assets.append({"type": "video", "path": item, "keyword": (keywords or ["viral"])[idx % max(1, len(keywords or ["viral"]))]})

    # Fill remaining assets with local dynamic motion backgrounds.
    needed = max(0, num_assets - len(assets))
    for i in range(needed):
        out_path = os.path.join(output_dir, f"motion_{i}.mp4")
        dur = random.randint(6, 10)
        ok = _create_motion_background(out_path, duration=dur, seed=i)
        if ok and os.path.exists(out_path):
            assets.append({"type": "video", "path": out_path, "keyword": (keywords or ["viral"])[i % max(1, len(keywords or ["viral"]))]})

    # Last-resort fallback to image generator if ffmpeg creation fails.
    if not assets:
        for img in generate_background_images(keywords, output_dir, num_images=max(1, num_assets), style="cinematic", dry_run=dry_run):
            assets.append({"type": "image", "path": img, "keyword": "fallback"})

    return assets


def generate_background_images(keywords, output_dir, num_images=5, style="cinematic", dry_run=True):
    os.makedirs(output_dir, exist_ok=True)
    images = []

    if dry_run:
        for i, kw in enumerate((keywords or ["viral"])[:num_images]):
            path = os.path.join(output_dir, f"bg_{i}_{kw.replace(' ', '_')}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"placeholder image for {kw} style={style}\n")
            images.append(path)
        return images

    try:
        import requests
    except Exception:
        # Fallback to placeholders if requests isn't available
        for i, kw in enumerate((keywords or ["viral"])[:num_images]):
            path = os.path.join(output_dir, f"bg_{i}_{kw.replace(' ', '_')}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"fallback image placeholder for {kw} style={style}\n")
            images.append(path)
        return images

    style_suffix = {
        "cinematic": "cinematic photography, dramatic lighting, 8k",
        "abstract": "abstract art, colorful, geometric, modern",
        "documentary": "documentary photography, realistic, sharp",
        "animated": "animation style, vibrant colors, clean",
    }.get(style, "cinematic photography, dramatic lighting, 8k")

    for i, keyword in enumerate((keywords or ["viral"])[:num_images]):
        prompt = f"{keyword}, {style_suffix}, vertical 9:16 composition, no text, professional"
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?width=1080&height=1920&seed={i*42}&nologo=true"
        img_path = os.path.join(output_dir, f"bg_{i}.jpg")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(img_path, "wb") as f:
                f.write(response.content)
            images.append(img_path)
        except Exception:
            # Network/provider fallback requested by user instructions.
            picsum_url = f"https://picsum.photos/1080/1920?seed={i*42+1}"
            try:
                fallback_response = requests.get(picsum_url, timeout=20)
                fallback_response.raise_for_status()
                with open(img_path, "wb") as f:
                    f.write(fallback_response.content)
                images.append(img_path)
            except Exception:
                fallback = os.path.join(output_dir, f"bg_{i}_{keyword.replace(' ', '_')}.txt")
                with open(fallback, "w", encoding="utf-8") as f:
                    f.write(f"network fallback image placeholder for {keyword} style={style}\n")
                images.append(fallback)
        time.sleep(1)

    return images
