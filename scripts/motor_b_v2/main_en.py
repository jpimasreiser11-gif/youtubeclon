import os
import sys
import time
from typing import Dict, Any

from scriptwriter_en import generate_script_en
from voice_en import generate_narration_en
from footage_fetcher import FootageFetcher
from assembler_en import assemble_mystery_video
from publisher import upload_to_youtube


def _gpu_ok() -> bool:
    try:
        import torch
        return torch.cuda.is_available()
    except Exception:
        return False


def _generate_fallback_ai_images(prompts, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, _ in enumerate(prompts):
        p = os.path.join(out_dir, f"ai_{i:02d}.jpg")
        # Placeholder visual fallback to keep pipeline operational.
        import subprocess
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=#202020:s=1080x1920:d=1", "-frames:v", "1", p
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        paths.append(p)
    return paths


def generate_mystery_video_en(topic: str = None, category: str = "mystery", duration_sec: int = 65, output_dir: str = "output") -> Dict[str, Any]:
    ts = int(time.time())
    work_dir = os.path.join(output_dir, f"en_{category}_{ts}")
    os.makedirs(work_dir, exist_ok=True)

    print("=" * 56)
    print("MOTOR B V2 ENGLISH GENERATOR")
    print("=" * 56)

    print("[1/6] Script generation")
    script_data = generate_script_en(topic=topic, category=category, duration_sec=duration_sec)

    with open(os.path.join(work_dir, "script.txt"), "w", encoding="utf-8") as f:
        f.write(script_data["script"])

    print("[2/6] Voice generation")
    device = "cuda" if _gpu_ok() else "cpu"
    narration = generate_narration_en(script_data["script"], os.path.join(work_dir, "audio"), device=device)

    print("[3/6] Real footage fetch")
    fetcher = FootageFetcher()
    footage = fetcher.fetch_batch_for_script(script_data["visual_prompts"], category, os.path.join(work_dir, "footage"))

    print("[4/6] AI image fallback for missing scenes")
    ai_prompts = [x["prompt"] for x in footage if x.get("type") == "ai_needed"]
    ai_images = _generate_fallback_ai_images(ai_prompts, os.path.join(work_dir, "ai_images")) if ai_prompts else []

    print("[5/6] Video assembly")
    final_video = os.path.join(work_dir, f"final_{category}_{ts}.mp4")
    # Optional local music path if available
    music_path = os.getenv("MOTOR_B_MUSIC_PATH", "")
    assemble_mystery_video(
        footage_clips=footage,
        ai_images=ai_images,
        narration_path=narration,
        music_path=music_path,
        output_path=final_video,
        category=category,
    )

    print("[6/6] YouTube publish (best effort)")
    publish = upload_to_youtube(
        video_path=final_video,
        title=script_data["title_a"],
        description_hook=script_data["description_hook"],
        tags=script_data["tags"],
    )

    print("Done")
    return {
        "work_dir": work_dir,
        "final_video": final_video,
        "publish": publish,
        "script_data": script_data,
    }


if __name__ == "__main__":
    t = sys.argv[1] if len(sys.argv) > 1 else None
    c = sys.argv[2] if len(sys.argv) > 2 else "mystery"
    d = int(sys.argv[3]) if len(sys.argv) > 3 else 65
    res = generate_mystery_video_en(topic=t, category=c, duration_sec=d)
    print(res["final_video"])
