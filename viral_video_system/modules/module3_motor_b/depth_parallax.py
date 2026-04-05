import os
import math
from typing import Optional

import cv2
import numpy as np


def _estimate_depth_map(image_bgr: np.ndarray) -> np.ndarray:
    """Estimate depth map in [0,1].

    If transformers Depth-Anything is available, use it.
    Otherwise fallback to luminance-based pseudo-depth.
    """
    try:
        from PIL import Image
        from transformers import pipeline

        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        depth_pipe = pipeline(task="depth-estimation", model="LiheYoung/depth-anything-small-hf")
        out = depth_pipe(pil)
        depth_img = np.array(out["depth"], dtype=np.float32)
        depth_img = cv2.resize(depth_img, (image_bgr.shape[1], image_bgr.shape[0]), interpolation=cv2.INTER_LINEAR)
        mn, mx = float(depth_img.min()), float(depth_img.max())
        if mx - mn < 1e-6:
            return np.full_like(depth_img, 0.5, dtype=np.float32)
        return (depth_img - mn) / (mx - mn)
    except Exception:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        # Slight blur to avoid noisy depth edges in fallback mode.
        return cv2.GaussianBlur(gray, (0, 0), 5)


def _safe_center_crop(img: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
    h, w = img.shape[:2]
    target_ar = target_w / max(1, target_h)
    src_ar = w / max(1, h)

    if src_ar >= target_ar:
        crop_h = h
        crop_w = int(crop_h * target_ar)
    else:
        crop_w = w
        crop_h = int(crop_w / target_ar)

    x = max(0, (w - crop_w) // 2)
    y = max(0, (h - crop_h) // 2)
    crop = img[y:y + crop_h, x:x + crop_w]
    return cv2.resize(crop, (target_w, target_h), interpolation=cv2.INTER_LINEAR)


def create_parallax_clip(
    image_path: str,
    output_path: str,
    duration: float = 8.0,
    fps: int = 30,
    width: int = 1080,
    height: int = 1920,
) -> Optional[str]:
    img = cv2.imread(image_path)
    if img is None:
        return None

    img = _safe_center_crop(img, width, height)
    depth = _estimate_depth_map(img)

    fg_mask = (depth > 0.56).astype(np.float32)
    fg_mask = cv2.GaussianBlur(fg_mask, (0, 0), 4)
    fg_mask = np.clip(fg_mask[..., None], 0.0, 1.0)

    bg = cv2.GaussianBlur(img, (0, 0), 1.2)
    fg = img.copy()

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    total_frames = max(1, int(duration * fps))

    for i in range(total_frames):
        t = i / max(1, total_frames - 1)
        # Ease in/out camera move for cinematic parallax.
        phase = math.sin(t * math.pi)

        bg_dx = int(round((phase - 0.5) * 14))
        bg_dy = int(round(math.sin(t * math.pi * 0.75) * 8))
        fg_dx = int(round((phase - 0.5) * 42))
        fg_dy = int(round(math.sin(t * math.pi * 0.75) * 20))

        bg_shift = np.roll(bg, shift=(bg_dy, bg_dx), axis=(0, 1))
        fg_shift = np.roll(fg, shift=(fg_dy, fg_dx), axis=(0, 1))

        frame = (fg_shift.astype(np.float32) * fg_mask) + (bg_shift.astype(np.float32) * (1.0 - fg_mask))
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        writer.write(frame)

    writer.release()
    return output_path if os.path.exists(output_path) else None
