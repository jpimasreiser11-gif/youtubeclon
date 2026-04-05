import cv2
import mediapipe as mp
import argparse
import os
import json
import numpy as np
from moviepy import VideoFileClip, vfx

class SmartCropper:
    def __init__(self, alpha=0.1, deadzone=0.02):
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            model_selection=1, min_detection_confidence=0.5
        )
        self.alpha = alpha  # Smoothing factor (EMA)
        self.deadzone = deadzone
        self.last_center_x = 0.5 # Normalized

    def get_face_center(self, image):
        results = self.face_detection.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if not results.detections:
            return None
        
        # Pick the largest face (closest to camera)
        best_detection = max(results.detections, key=lambda det: det.location_data.relative_bounding_box.width)
        bbox = best_detection.location_data.relative_bounding_box
        center_x = bbox.xmin + (bbox.width / 2)
        return center_x

    def analyze_faces(self, input_path, sample_rate=5):
        """Analyze face positions every X frames to build a tracking path"""
        cap = cv2.VideoCapture(input_path)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        tracking_data = []
        frame_idx = 0
        
        print(f"🕵️ Analyzing {total_frames} frames for face tracking...")
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            if frame_idx % sample_rate == 0:
                face_x = self.get_face_center(frame)
                if face_x is not None:
                    # Smoothing
                    if self.last_center_x is None:
                        self.last_center_x = face_x
                    else:
                        if abs(face_x - self.last_center_x) > self.deadzone:
                            self.last_center_x = self.alpha * face_x + (1 - self.alpha) * self.last_center_x
                    
                    tracking_data.append({
                        "t": round(frame_idx / fps, 3),
                        "x": round(self.last_center_x, 4)
                    })
            
            frame_idx += 1
            if frame_idx % 100 == 0:
                print(f"  Progress: {frame_idx}/{total_frames} frames")
                
        cap.release()
        return tracking_data, w, h, fps

    def apply_ffmpeg_crop(self, input_path, output_path, tracking_data, w, h):
        """Build and run a high-performance FFmpeg command for dynamic cropping"""
        target_w = int(h * (9/16))
        if target_w > w: target_w = w
        
        # Build complex filter for dynamic X-coordinate
        # We use a series of 'if(between(t, START, END), VALUE)' or we can just use a simpler approach if many points:
        # For simplicity in this script, we'll use a smooth EMA-based constant for segments
        # or use the 'sendcmd' filter. For a robust solution, we'll build a long expression string.
        
        x_expr = ""
        for i in range(len(tracking_data)):
            t_start = tracking_data[i]['t']
            t_end = tracking_data[i+1]['t'] if i+1 < len(tracking_data) else 9999
            center_px = int(tracking_data[i]['x'] * w)
            x1 = max(0, min(w - target_w, center_px - (target_w // 2)))
            
            x_expr += f"if(between(t,{t_start},{t_end}),{x1},"
        
        x_expr += "0" + (")" * len(tracking_data))
        
        filter_str = f"crop={target_w}:{h}:{x_expr}:0"
        
        import subprocess
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-vf', filter_str,
            '-c:v', 'libx264', 
            '-crf', '18',              # MAX QUALITY (Lower is better, 18 is visually lossless)
            '-preset', 'slow',         # MUCH better quality/compression ratio than ultrafast
            '-profile:v', 'high',      # High profile for social media
            '-pix_fmt', 'yuv420p',     # Required for TikTok/IG compatibility
            '-c:a', 'aac', '-b:a', '192k', # Better audio quality
            output_path
        ]
        
        print(f"🎬 Executing FFmpeg Smart Crop (MAX QUALITY 9:16)...")
        subprocess.run(cmd, check=True)
        return output_path

    def process_video(self, input_path, output_path):
        tracking_data, w, h, fps = self.analyze_faces(input_path)
        if not tracking_data:
            print("⚠️ No faces detected, performing static center crop.")
            tracking_data = [{"t": 0, "x": 0.5}]
            
        self.apply_ffmpeg_crop(input_path, output_path, tracking_data, w, h)
        
        return {
            "status": "success",
            "output": output_path,
            "tracking_points": len(tracking_data)
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sovereign Smart Cropper")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--alpha", type=float, default=0.1)
    
    args = parser.parse_args()
    
    cropper = SmartCropper(alpha=args.alpha)
    result = cropper.process_video(args.input, args.output)
    print(json.dumps(result))
