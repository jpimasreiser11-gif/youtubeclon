"""
Active Speaker Detection (ASD) and Smart Reframing module.
Uses MediaPipe Tasks API (Face Landmarker) to track the active speaker.
"""
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import os
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

@dataclass
class SpeakerState:
    center_x: float
    center_y: float
    mar: float
    face_id: int

class ActiveSpeakerDetector:
    def __init__(self, model_path='data/face_landmarker.task', alpha=0.1, mar_threshold=0.3):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"MediaPipe model not found at {model_path}. Please download it first.")
            
        self.base_options = python.BaseOptions(model_asset_path=model_path)
        self.options = vision.FaceLandmarkerOptions(
            base_options=self.base_options,
            output_face_blendshapes=True,
            output_facial_transformation_matrixes=True,
            num_faces=5
        )
        self.detector = vision.FaceLandmarker.create_from_options(self.options)
        
        self.alpha = alpha  # Smoothing factor for EMA
        self.mar_threshold = mar_threshold
        self.last_center_x = None
        self.last_center_y = None

    def calculate_distance(self, p1, p2):
        return np.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

    def calculate_mar(self, landmarks):
        """
        Calculate Mouth Aspect Ratio (MAR) using Face Landmarker landmarks.
        Indices (canonical):
        - Corners: 61, 291
        - Upper: 37, 0, 267
        - Lower: 84, 17, 314
        """
        try:
            # Corners
            p61 = landmarks[61]
            p291 = landmarks[291]
            
            # Vertical pairs
            p37 = landmarks[37]
            p84 = landmarks[84]
            p0 = landmarks[0]
            p17 = landmarks[17]
            p267 = landmarks[267]
            p314 = landmarks[314]

            v1 = self.calculate_distance(p37, p84)
            v2 = self.calculate_distance(p0, p17)
            v3 = self.calculate_distance(p267, p314)
            h = self.calculate_distance(p61, p291)

            if h == 0: return 0
            mar = (v1 + v2 + v3) / (3.0 * h)
            return mar
        except Exception as e:
            return 0

    def get_top_speakers(self, frame_rgb, top_k=2):
        """Detect faces and identify top speakers"""
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = self.detector.detect(mp_image)
        
        if not result.face_landmarks:
            return []

        speakers = []
        for idx, face_landmarks in enumerate(result.face_landmarks):
            mar = self.calculate_mar(face_landmarks)
            all_x = [lm.x for lm in face_landmarks]
            all_y = [lm.y for lm in face_landmarks]
            center_x = sum(all_x) / len(all_x)
            center_y = sum(all_y) / len(all_y)
            
            # Simple bounding box for size heuristic
            face_w = max(all_x) - min(all_x)
            face_h = max(all_y) - min(all_y)
            
            speakers.append({
                "center": (center_x, center_y),
                "mar": mar,
                "size": face_w * face_h,
                "id": idx
            })

        # Sort by MAR (talkingness) then by size
        # We want to identify the people who are actually talking
        speakers = sorted(speakers, key=lambda x: x['mar'], reverse=True)
        return speakers[:top_k]

    def get_speaker_center(self, frame_rgb):
        """Legacy compatibility: returns the single best speaker center"""
        speakers = self.get_top_speakers(frame_rgb, top_k=1)
        if speakers and speakers[0]['mar'] > self.mar_threshold:
            return speakers[0]['center']
        return None

    def smooth_center(self, current_center):
        """Apply EMA smoothing to crop center"""
        if current_center is None:
            # If no speaker detected, stick to last known or center
            return (self.last_center_x, self.last_center_y) if self.last_center_x is not None else (0.5, 0.5)

        curr_x, curr_y = current_center

        if self.last_center_x is None:
            self.last_center_x = curr_x
            self.last_center_y = curr_y
        else:
            self.last_center_x = self.alpha * curr_x + (1 - self.alpha) * self.last_center_x
            self.last_center_y = self.alpha * curr_y + (1 - self.alpha) * self.last_center_y

        return (self.last_center_x, self.last_center_y)

    def process_video_segment(self, video_path, start_time, end_time, fps_sample=5):
        """
        Analyze a video segment and return:
        - centers: Timestamp -> smoothed_center (legacy)
        - multi_speaker_track: Timestamp -> list of top speakers
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return {}, {}

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps / fps_sample) if fps > fps_sample else 1
        cap.set(cv2.CAP_PROP_POS_MSEC, start_time * 1000)
        
        centers = {}
        multi_track = {}
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
                
            curr_pos_sec = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
            if curr_pos_sec > end_time: break
                
            if frame_count % frame_interval == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # New multi-speaker tracking
                top_speakers = self.get_top_speakers(frame_rgb)
                multi_track[curr_pos_sec] = top_speakers
                
                # Single speaker smoothing (legacy)
                raw_center = top_speakers[0]['center'] if top_speakers and top_speakers[0]['mar'] > self.mar_threshold else None
                smoothed_center = self.smooth_center(raw_center)
                centers[curr_pos_sec] = smoothed_center
                
            frame_count += 1
            
        cap.release()
        return centers, multi_track

def get_crop_track(video_path, start_time, end_time):
    """Convenience function to get smoothed tracking data"""
    detector = ActiveSpeakerDetector()
    centers, _ = detector.process_video_segment(video_path, start_time, end_time)
    return centers

def get_multi_speaker_track(video_path, start_time, end_time):
    """Convenience function to get full multi-speaker data"""
    detector = ActiveSpeakerDetector()
    _, multi_track = detector.process_video_segment(video_path, start_time, end_time)
    return multi_track

if __name__ == "__main__":
    test_video = "data/jNQXAC9IVRw.mp4"
    if os.path.exists(test_video):
        print(f"Testing modern ASD on {test_video}...")
        try:
            track = get_crop_track(test_video, 0, 5)
            print(f"Successfully tracked {len(track)} points.")
            for t, center in list(track.items())[:5]:
                print(f"  Time {t:.2f}s -> Center {center[0]:.3f}, {center[1]:.3f}")
        except Exception as e:
            print(f"Error during ASD test: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Test video not found. Skipping local test.")
