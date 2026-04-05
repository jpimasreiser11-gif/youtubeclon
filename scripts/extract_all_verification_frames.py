import cv2
import os

def extract_all():
    output_dir = 'output/final_verification'
    os.makedirs(output_dir, exist_ok=True)
    
    for i in range(3):
        video_path = f'output/jNQXAC9IVRw_clip_{i}.mp4'
        if not os.path.exists(video_path):
            print(f"Skipping {video_path}, not found.")
            continue
            
        print(f"Extracting from {video_path}...")
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Error: Could not open {video_path}")
            continue

        # Extract at 2s and 10s for each clip
        for t in [2, 10]:
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ret, frame = cap.read()
            if ret:
                out_file = f"{output_dir}/clip_{i}_at_{t}s.jpg"
                cv2.imwrite(out_file, frame)
                print(f"Saved: {out_file}")
            else:
                print(f"Failed to read clip {i} at {t}s")
        
        cap.release()

if __name__ == "__main__":
    extract_all()
