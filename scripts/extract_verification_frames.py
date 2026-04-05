import cv2
import os

def extract():
    video_path = 'output/jNQXAC9IVRw_clip_0.mp4'
    output_dir = 'output/frames_asd'
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open {video_path}")
        return

    times = [2, 5, 10]
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ret, frame = cap.read()
        if ret:
            out_file = f"{output_dir}/frame_at_{t}s.jpg"
            cv2.imwrite(out_file, frame)
            print(f"Saved: {out_file}")
        else:
            print(f"Failed to read at {t}s")
    
    cap.release()

if __name__ == "__main__":
    extract()
