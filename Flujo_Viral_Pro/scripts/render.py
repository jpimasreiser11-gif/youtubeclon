import os
import argparse
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
import moviepy.video.fx.all as vfx

def create_video(audio_path, video_path, output_path):
    print(f"Loading audio: {audio_path}")
    audio = AudioFileClip(audio_path)
    
    print(f"Loading video: {video_path}")
    video = VideoFileClip(video_path)

    # 1. Loop video if shorter than audio
    if video.duration < audio.duration:
        n_loops = int(audio.duration // video.duration) + 1
        video = concatenate_videoclips([video] * n_loops)
    
    # 2. Trim to exact audio duration
    video = video.subclip(0, audio.duration)
    video = video.set_audio(audio)

    # 3. Resize/Crop to 9:16 Vertical (1080x1920)
    w, h = video.size
    target_ratio = 9/16
    current_ratio = w/h

    if current_ratio > target_ratio:
        # Too wide, crop width from center
        new_w = h * target_ratio
        video = video.crop(x1=(w/2 - new_w/2), width=new_w, height=h)
    else:
        # Too tall, crop height from center
        new_h = w / target_ratio
        video = video.crop(y1=(h/2 - new_h/2), width=w, height=new_h)
    
    video = video.resize(height=1920) 

    # 4. Transcribe with Whisper
    print("Transcribing audio for subtitles (Whisper base model)...")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, word_timestamps=True)
    
    # 5. Generate Word-Level Subtitles
    subtitle_clips = []
    print("Generating subtitle overlays...")
    for segment in result["segments"]:
        for word in segment["words"]:
            start = word["start"]
            end = word["end"]
            text = word["word"].strip()
            
            # Note: TextClip requires ImageMagick installed and configured in MoviePy
            try:
                txt_clip = TextClip(
                    text, 
                    fontsize=100, 
                    color='yellow', 
                    font='Arial', 
                    stroke_color='black', 
                    stroke_width=4,
                    method='caption',
                    size=(800, None) # Width constraint
                )
                txt_clip = txt_clip.set_position(('center', 'center')).set_start(start).set_duration(end-start)
                subtitle_clips.append(txt_clip)
            except Exception as e:
                print(f"Warning: Could not create TextClip for word '{text}'. ensure ImageMagick is installed. Error: {e}")

    # 6. Composite
    final_video = CompositeVideoClip([video] + subtitle_clips)
    
    print(f"Rendering final video to {output_path}...")
    final_video.write_videofile(
        output_path, 
        fps=30, 
        codec="libx264", 
        audio_codec="aac",
        threads=4,
        preset="fast"
    )
    print("Render complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True)
    parser.add_argument("--video", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    create_video(args.audio, args.video, args.output)
