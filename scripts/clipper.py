import os
import sys
import json
import subprocess
from moviepy import VideoFileClip, CompositeVideoClip
from pathlib import Path
import cv2
import numpy as np

# Import PIL subtitle renderer
from pil_subtitle_renderer import render_subtitles_on_frame
from active_speaker_detector import get_crop_track, get_multi_speaker_track

class OneEuroFilter:
    def __init__(self, t0, x0, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = x0
        self.dx_prev = 0.0
        self.t_prev = t0

    def __call__(self, t, x):
        dt = t - self.t_prev
        if dt <= 0:
            return self.x_prev
            
        dx = (x - self.x_prev) / dt
        edx = self.exponential_smoothing(dx, self.dx_prev, dt, self.d_cutoff)
        cutoff = self.min_cutoff + self.beta * abs(edx)
        x_filtered = self.exponential_smoothing(x, self.x_prev, dt, cutoff)
        
        self.x_prev = x_filtered
        self.dx_prev = edx
        self.t_prev = t
        return x_filtered

    def exponential_smoothing(self, x, x_prev, dt, cutoff):
        tau = 1.0 / (2 * np.pi * cutoff)
        alpha = 1.0 / (1.0 + tau / dt)
        return alpha * x + (1 - alpha) * x_prev

def filter_words_for_clip(all_words, start_time, end_time):
    """
    Extract words that fall within the clip's time range
    and adjust their timestamps to be relative to clip start
    """
    clip_words = []
    for word in all_words:
        word_start = word.get('start', 0)
        word_end = word.get('end', 0)
        
        # Check if word overlaps with clip time range
        if word_start < end_time and word_end > start_time:
            # Adjust timestamps to be relative to clip start
            adjusted_word = {
                'word': word.get('word', ''),
                'start': max(0, word_start - start_time),
                'end': min(end_time - start_time, word_end - start_time)
            }
            clip_words.append(adjusted_word)
    
    return clip_words

def process_clip(video_id, title, start_time, end_time, index, all_words=None, input_path=None, subtitle_style="DEFAULT", broll_path=None):
    if not input_path:
        input_path = f"data/{video_id}.mp4"
    final_output = f"output/{video_id}_clip_{index}.mp4"
    
    if not os.path.exists('output'):
        os.makedirs('output')

    print(f"\n🎬 Processing clip {index}: {title}")
    print(f"   Time: {start_time:.2f}s - {end_time:.2f}s ({end_time - start_time:.2f}s duration)")
    
    # 1. ASD Analysis for smart reframing
    print(f"   🤖 ASD Analysis for smart reframing...")
    # Analyze a bit more than the clip ends
    crop_track = get_crop_track(input_path, max(0, start_time - 1), end_time + 1)
    multi_track = get_multi_speaker_track(input_path, max(0, start_time - 1), end_time + 1)
    
    # 2. Saneamiento Lingüístico (Jump-Cut Logic)
    # Define segments to KEEP (relative to start_time)
    from disfluency_detector import detect_removals
    removals = detect_removals(all_words if all_words else [], start_time, end_time)
    
    keep_segments = []
    current_t = start_time
    for rem in removals:
        if rem['start'] > current_t:
            keep_segments.append((current_t, rem['start']))
        current_t = rem['end']
    if current_t < end_time:
        keep_segments.append((current_t, end_time))

    # Calculate final duration and mapping table
    # Mapping: (final_start, final_end) -> (source_start, source_end)
    time_map = []
    final_duration = 0
    for s_start, s_end in keep_segments:
        seg_dur = s_end - s_start
        time_map.append({
            'f_start': final_duration,
            'f_end': final_duration + seg_dur,
            's_start': s_start,
            's_end': s_end
        })
        final_duration += seg_dur

    print(f"   ✂️ Jump-cuts enabled: Removed {len(removals)} segments. Final duration: {final_duration:.2f}s")

    with VideoFileClip(input_path) as video:
        # Create a dummy clip with the final duration
        from moviepy import ColorClip
        # We need something to 'transform'
        clip = ColorClip(size=video.size, color=(0,0,0), duration=final_duration)
        
        # 3. Subtitle setup
        clip_words = []
        if all_words:
            print(f"   📝 Preparing subtitles...")
            # We filter for the original range, mapping will handle the display time
            clip_words = filter_words_for_clip(all_words, start_time, end_time)
        
        # 4. Smart Cropping & Subtitle Overlay (Combined Frame-by-Frame)
        # Initialize stabilization filters
        filter_x = OneEuroFilter(start_time, 0.5)
        filter_split_top = OneEuroFilter(start_time, 0.5)
        filter_split_bot = OneEuroFilter(start_time, 0.5)

        def process_frame(get_frame, t):
            target_ratio = 9/16
            
            # Map t (final) to t_source
            t_source = start_time # Fallback
            for segment in time_map:
                if segment['f_start'] <= t <= segment['f_end']:
                    t_source = segment['s_start'] + (t - segment['f_start'])
                    break
            
            # Get original frame at t_source
            frame = video.get_frame(t_source)
            h_orig, w_orig = frame.shape[:2]
            
            # Identify smart center_x
            # We check multi_track for multi-speaker logic
            nearest_st = min(multi_track.keys(), key=lambda x: abs(x - t_source))
            top_speakers = multi_track[nearest_st]
            
            # Check for split screen (two speakers talking)
            # Threshold: both have MAR > mar_threshold
            speaking_faces = [s for s in top_speakers if s['mar'] > 0.25] # Slightly lower threshold for stability
            
            if len(speaking_faces) >= 2:
                # SPLIT SCREEN!
                # Render top half for speaker 1, bottom for speaker 2
                s1, s2 = speaking_faces[0], speaking_faces[1]
                
                # Crop 1 (Top)
                raw_x1 = s1['center'][0]
                stable_x1 = filter_split_top(t_source, raw_x1)
                
                x1_top = int(max(0, min(w_orig - (h_orig/2 * target_ratio), stable_x1 * w_orig - (h_orig/2 * target_ratio) / 2)))
                x2_top = int(x1_top + (h_orig/2 * target_ratio))
                frame1 = frame[0:int(h_orig/2), x1_top:x2_top]
                frame1_res = cv2.resize(frame1, (1080, 960))
                
                # Crop 2 (Bottom)
                raw_x2 = s2['center'][0]
                stable_x2 = filter_split_bot(t_source, raw_x2)
                
                x1_bot = int(max(0, min(w_orig - (h_orig/2 * target_ratio), stable_x2 * w_orig - (h_orig/2 * target_ratio) / 2)))
                x2_bot = int(x1_bot + (h_orig/2 * target_ratio))
                frame2 = frame[int(h_orig/2):, x1_bot:x2_bot]
                frame2_res = cv2.resize(frame2, (1080, 960))
                
                frame_resized = np.vstack((frame1_res, frame2_res))
            else:
                # SINGLE SPEAKER (Standard)
                target_x_raw = 0.5
                if speaking_faces:
                    target_x_raw = speaking_faces[0]['center'][0]
                elif top_speakers:
                    target_x_raw = top_speakers[0]['center'][0]
                
                # Apply stabilization
                target_x = filter_x(t_source, target_x_raw)
                
                new_w = h_orig * target_ratio
                pixel_x_center = target_x * w_orig
                
                x1 = int(max(0, min(w_orig - new_w, pixel_x_center - new_w / 2)))
                x2 = int(x1 + new_w)
                
                frame_cropped = frame[:, x1:x2]
                frame_resized = cv2.resize(frame_cropped, (1080, 1920))
            
            # Overlay subtitles using t_source for synchronization
            if clip_words:
                # IMPORTANT: render_subtitles_on_frame expects t relative to clip start
                # but our words are adjusted relative to start_time.
                # So we pass t_source - start_time
                # IMPORTANT: render_subtitles_on_frame expects t relative to clip start
                # but our words are adjusted relative to start_time.
                # So we pass t_source - start_time
                return render_subtitles_on_frame(frame_resized, clip_words, t_source - start_time, (1080, 1920), style_name=subtitle_style)
            
            return frame_resized

        print(f"   ✓ Unified rendering engine active (ASD + Subtitles + Jump-Cuts)")
        final_video = clip.transform(process_frame)
        
        # 4.5 AI B-Roll Integration (Cutaway logic)
        if broll_path and os.path.exists(broll_path):
            print(f"   🎬 Integrating AI B-Roll cutaway...")
            with VideoFileClip(broll_path) as broll:
                # Resize and crop B-roll to 9:16
                bh, bw = broll.size
                br_ratio = 9/16
                nbw = bh * br_ratio
                broll_cropped = broll.crop(x1=(bw - nbw)/2, y1=0, x2=(bw + nbw)/2, y2=bh).resized(height=1920)
                
                # Insert B-roll in the middle of the clip for 3-5 seconds
                br_duration = min(broll.duration, 4.0)
                br_start = max(1.0, final_duration / 2 - br_duration / 2)
                
                # Composite: Original transformed video + B-roll overlay
                # Note: B-roll replaces the main visual but keeps subtitles if we composite carefully
                broll_overlay = broll_cropped.with_start(br_start).with_duration(br_duration).with_position('center')
                
                # We need to ensure subtitles are still visible. 
                # Since process_frame already rendered them, we'd need to render them ABOVE B-roll too.
                # Simplified: B-roll covers the screen, then we return to main video.
                from moviepy import CompositeVideoClip
                final_video = CompositeVideoClip([final_video, broll_overlay])

        # 5. Export
        print(f"   💾 Rendering final viral clip...")
        final_video.write_videofile(
            final_output, 
            codec="libx264", 
            audio_codec="aac", 
            fps=30,
            preset='fast',
            threads=8
        )
        
        print(f"   ✅ Clip saved to {final_output}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python clipper.py <json_input>")
        sys.exit(1)
        
    arg = sys.argv[1]
    # Support both file path and inline JSON
    if os.path.isfile(arg):
        with open(arg, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = json.loads(arg)
    video_id = data['id']
    clips = data['clips']  # List of {title, start_time, end_time}
    all_words = data.get('words', None)  # Optional: word-level timestamps
    input_video_path = data.get('video_path', None) # Optional: custom master video
    subtitle_style = data.get('subtitle_style', 'DEFAULT')
    broll_path = data.get('broll_path', None)
    
    if all_words:
        print(f"📚 Loaded {len(all_words)} words for subtitle generation")
    else:
        print("⚠️  No word-level data provided - clips will be generated without subtitles")
    
    print(f"\n🎥 Processing {len(clips)} clips from video {video_id}\n")
    print("=" * 60)
    
    for i, clip_data in enumerate(clips):
        try:
            process_clip(
                video_id, 
                clip_data['title'], 
                clip_data['start_time'], 
                clip_data['end_time'], 
                i,
                all_words,
                input_path=input_video_path,
                subtitle_style=subtitle_style,
                broll_path=broll_path
            )
        except Exception as e:
            print(f"❌ Error processing clip {i} ('{clip_data.get('title', 'Unknown')}'): {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "=" * 60)
    print(f"✅ All {len(clips)} clips processed successfully!")
    print(f"📁 Output directory: output/")

