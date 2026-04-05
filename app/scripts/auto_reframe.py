"""Dynamic auto-reframe with MediaPipe nose tracking.

Tracks the active speaker's nose frame-by-frame and keeps it near the
upper-center area of a 9:16 frame.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np


mp_face_mesh = mp.solutions.face_mesh


@dataclass
class TrackingPoint:
    time: float
    x: float
    y: float
    score: float


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _mouth_openness(face_landmarks) -> float:
    top_lip = face_landmarks.landmark[13]
    bot_lip = face_landmarks.landmark[14]
    return abs(bot_lip.y - top_lip.y)


def _face_size_proxy(face_landmarks) -> float:
    l = face_landmarks.landmark[234]
    r = face_landmarks.landmark[454]
    return abs(r.x - l.x)


def _pick_active_speaker(faces) -> Optional[Tuple[float, float, float]]:
    best = None
    best_score = -1.0
    for face in faces:
        nose = face.landmark[1]
        openness = _mouth_openness(face)
        size = _face_size_proxy(face)
        score = (openness * 3.0) + size
        if score > best_score:
            best_score = score
            best = (nose.x, nose.y, score)
    return best


def detect_nose_tracking_path(
    video_path: str,
    sample_every_n_frames: int = 1,
    min_detection_confidence: float = 0.55,
    min_tracking_confidence: float = 0.55,
    smooth_alpha: float = 0.25,
) -> List[TrackingPoint]:
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    points: List[TrackingPoint] = []
    prev_x = 0.5
    prev_y = 0.35

    with mp_face_mesh.FaceMesh(
        static_image_mode=False,
        max_num_faces=4,
        refine_landmarks=True,
        min_detection_confidence=min_detection_confidence,
        min_tracking_confidence=min_tracking_confidence,
    ) as face_mesh:
        frame_idx = 0
        while cap.isOpened():
            ok, frame = cap.read()
            if not ok:
                break

            if sample_every_n_frames > 1 and frame_idx % sample_every_n_frames != 0:
                frame_idx += 1
                continue

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = face_mesh.process(rgb)

            t = frame_idx / fps
            if result.multi_face_landmarks:
                active = _pick_active_speaker(result.multi_face_landmarks)
                if active is not None:
                    x, y, score = active
                    # EMA smoothing to avoid jitter when subject moves.
                    x = (smooth_alpha * x) + ((1.0 - smooth_alpha) * prev_x)
                    y = (smooth_alpha * y) + ((1.0 - smooth_alpha) * prev_y)
                    prev_x, prev_y = x, y
                    points.append(TrackingPoint(time=t, x=x, y=y, score=score))
                else:
                    points.append(TrackingPoint(time=t, x=prev_x, y=prev_y, score=0.0))
            else:
                points.append(TrackingPoint(time=t, x=prev_x, y=prev_y, score=0.0))

            frame_idx += 1

    cap.release()

    if not points and total_frames > 0:
        duration = max(1.0, total_frames / fps)
        points = [TrackingPoint(time=0.0, x=0.5, y=0.35, score=0.0), TrackingPoint(time=duration, x=0.5, y=0.35, score=0.0)]

    return points


def _interpolate_tracking(points: List[TrackingPoint], t: float) -> TrackingPoint:
    if not points:
        return TrackingPoint(time=t, x=0.5, y=0.35, score=0.0)
    if t <= points[0].time:
        return points[0]
    if t >= points[-1].time:
        return points[-1]

    lo = 0
    hi = len(points) - 1
    while lo + 1 < hi:
        mid = (lo + hi) // 2
        if points[mid].time <= t:
            lo = mid
        else:
            hi = mid

    a = points[lo]
    b = points[hi]
    dt = max(1e-6, b.time - a.time)
    p = (t - a.time) / dt
    return TrackingPoint(
        time=t,
        x=(a.x + (b.x - a.x) * p),
        y=(a.y + (b.y - a.y) * p),
        score=(a.score + (b.score - a.score) * p),
    )


def render_dynamic_reframe(
    input_video: str,
    output_video: str,
    start_time: float = 0.0,
    duration: Optional[float] = None,
    target_width: int = 1080,
    target_height: int = 1920,
    nose_anchor_y: float = 0.32,
) -> str:
    cap = cv2.VideoCapture(input_video)
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)

    if src_w <= 0 or src_h <= 0:
        cap.release()
        raise RuntimeError(f"Invalid video dimensions for {input_video}")

    start_frame = int(max(0.0, start_time) * fps)
    if duration is None:
        end_frame = total_frames
    else:
        end_frame = min(total_frames, start_frame + int(max(0.0, duration) * fps))

    tracking = detect_nose_tracking_path(input_video, sample_every_n_frames=1)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_video, fourcc, fps, (target_width, target_height))

    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    frame_idx = start_frame

    target_ar = target_width / max(1, target_height)
    src_ar = src_w / max(1, src_h)

    while frame_idx < end_frame:
        ok, frame = cap.read()
        if not ok:
            break

        t = frame_idx / fps
        p = _interpolate_tracking(tracking, t)

        if src_ar >= target_ar:
            crop_h = src_h
            crop_w = int(crop_h * target_ar)
        else:
            crop_w = src_w
            crop_h = int(crop_w / target_ar)

        nose_px_x = int(p.x * src_w)
        nose_px_y = int(p.y * src_h)

        crop_x = int(nose_px_x - (crop_w * 0.5))
        crop_y = int(nose_px_y - (crop_h * nose_anchor_y))
        crop_x = int(_clamp(crop_x, 0, max(0, src_w - crop_w)))
        crop_y = int(_clamp(crop_y, 0, max(0, src_h - crop_h)))

        crop = frame[crop_y:crop_y + crop_h, crop_x:crop_x + crop_w]
        if crop.size == 0:
            crop = frame

        out = cv2.resize(crop, (target_width, target_height), interpolation=cv2.INTER_LINEAR)
        writer.write(out)

        frame_idx += 1

    cap.release()
    writer.release()
    return output_video


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Dynamic nose-tracking auto reframe")
    parser.add_argument("input_video")
    parser.add_argument("output_video")
    parser.add_argument("--start", type=float, default=0.0)
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--width", type=int, default=1080)
    parser.add_argument("--height", type=int, default=1920)
    args = parser.parse_args()

    render_dynamic_reframe(
        input_video=args.input_video,
        output_video=args.output_video,
        start_time=args.start,
        duration=args.duration,
        target_width=args.width,
        target_height=args.height,
    )
