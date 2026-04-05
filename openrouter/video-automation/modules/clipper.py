import os
import json
import logging
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime

# Import config
from config import CLIPS_DIR, DOWNLOADS_DIR

# Initialize logger
logger = logging.getLogger(__name__)

class Clipper:
    def __init__(self):
        self.processed_videos = self.load_processed_videos()

    def load_processed_videos(self):
        """Load the list of already processed videos"""
        processed_file = os.path.join(CLIPS_DIR, "processed.json")
        if os.path.exists(processed_file):
            try:
                with open(processed_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading processed videos: {e}")
        return []

    def save_processed_videos(self):
        """Save the list of processed videos"""
        processed_file = os.path.join(CLIPS_DIR, "processed.json")
        try:
            with open(processed_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_videos, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving processed videos: {e}")

    def get_video_hash(self, video_path):
        """Generate a hash for the video file to check duplicates"""
        if not os.path.exists(video_path):
            return None
        try:
            # Use file size and modification time for quick hash
            stat = os.stat(video_path)
            hash_string = f"{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(hash_string.encode('utf-8')).hexdigest()
        except Exception:
            return None

    def is_already_processed(self, video_path):
        """Check if video is already processed"""
        video_hash = self.get_video_hash(video_path)
        return video_hash in self.processed_videos if video_hash else False

    def mark_as_processed(self, video_path):
        """Mark video as processed"""
        video_hash = self.get_video_hash(video_path)
        if video_hash:
            self.processed_videos.append(video_hash)
            self.save_processed_videos()

    def extract_audio(self, video_path, audio_path):
        """Extract audio from video using ffmpeg"""
        try:
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',  # PCM 16-bit
                '-ar', '16000',  # 16kHz sample rate
                '-ac', '1',  # Mono
                '-y',  # Overwrite output
                audio_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error extracting audio: {e}")
            return False

    def detect_active_segments(self, audio_path, duration):
        """Detect active audio segments using librosa"""
        try:
            import librosa
            import numpy as np

            # Load audio
            y, sr = librosa.load(audio_path, sr=None)

            # Compute short-time energy
            hop_length = 512
            energy = librosa.feature.rms(y=y, hop_length=hop_length)[0]
            times = librosa.times_like(energy, hop_length=hop_length, sr=sr)

            # Normalize energy
            energy_norm = (energy - np.min(energy)) / (np.max(energy) - np.min(energy) + 1e-8)

            # Find segments above threshold
            threshold = 0.3
            active = energy_norm > threshold

            # Find contiguous segments
            segments = []
            in_segment = False
            start_time = 0

            for i, is_active in enumerate(active):
                if is_active and not in_segment:
                    start_time = times[i]
                    in_segment = True
                elif not is_active and in_segment:
                    end_time = times[i]
                    if end_time - start_time >= 2.0:  # Minimum 2 seconds
                        segments.append((start_time, end_time))
                    in_segment = False

            # Handle case where segment ends at the end
            if in_segment:
                end_time = times[-1]
                if end_time - start_time >= 2.0:
                    segments.append((start_time, end_time))

            return segments
        except Exception as e:
            logger.error(f"Error detecting active segments: {e}")
            # Return middle segment as fallback
            return [(duration * 0.3, duration * 0.7)]

    def create_clip(self, video_path, start_time, end_time, output_path):
        """Create a clip from video using ffmpeg"""
        try:
            duration = end_time - start_time
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(start_time),
                '-t', str(duration),
                '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2',
                '-c:v', 'libx264',
                '-preset', 'medium',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-y',  # Overwrite output
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Error creating clip: {e}")
            return False

    def add_subtitles(self, video_path, output_path):
        """Add subtitles using faster-whisper and burn them into video"""
        try:
            from faster_whisper import WhisperModel

            # Extract audio for transcription
            audio_path = video_path.replace('.mp4', '_audio.wav')
            if not self.extract_audio(video_path, audio_path):
                return False

            # Transcribe audio
            model = WhisperModel("base", device="cpu", compute_type="int8")
            segments, info = model.transcribe(audio_path, beam_size=5)

            # Create subtitle file
            srt_path = video_path.replace('.mp4', '.srt')
            with open(srt_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(segments, start=1):
                    start = self.format_srt_time(segment.start)
                    end = self.format_srt_time(segment.end)
                    text = segment.text.strip()
                    f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

            # Burn subtitles into video
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles={srt_path}:force_style='Fontsize=24,PrimaryColour=&HFFFFFF&,BackColour=&H80000000&,BorderStyle=3,Outline=1,Shadow=0,Alignment=2,MarginV=50'",
                '-c:a', 'copy',
                '-y',  # Overwrite output
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)

            # Clean up temporary files
            try:
                os.remove(audio_path)
                os.remove(srt_path)
            except:
                pass

            return True
        except Exception as e:
            logger.error(f"Error adding subtitles: {e}")
            return False

    def format_srt_time(self, seconds):
        """Format seconds as SRT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def process_video(self, video_path):
        """Process a video to create clips"""
        if not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return []

        if self.is_already_processed(video_path):
            logger.info(f"Video already processed: {video_path}")
            return []

        # Get video duration
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            duration = float(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error getting video duration: {e}")
            duration = 60.0  # Default fallback

        # Extract audio
        audio_path = video_path.replace('.mp4', '_audio.wav')
        if not self.extract_audio(video_path, audio_path):
            return []

        # Detect active segments
        segments = self.detect_active_segments(audio_path, duration)

        # Clean up audio file
        try:
            os.remove(audio_path)
        except:
            pass

        # Create clips from active segments
        clips = []
        for i, (start_time, end_time) in enumerate(segments):
            # Ensure clip is between 45-60 seconds
            clip_duration = end_time - start_time
            if clip_duration < 45:
                # Extend to minimum 45 seconds
                extension = (45 - clip_duration) / 2
                start_time = max(0, start_time - extension)
                end_time = min(duration, end_time + extension)
            elif clip_duration > 60:
                # Trim to maximum 60 seconds
                start_time = start_time
                end_time = start_time + 60

            # Create clip
            clip_filename = f"clip_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i}.mp4"
            clip_path = os.path.join(CLIPS_DIR, clip_filename)

            if self.create_clip(video_path, start_time, end_time, clip_path):
                # Add subtitles
                final_clip_path = clip_path.replace('.mp4', '_final.mp4')
                if self.add_subtitles(clip_path, final_clip_path):
                    # Remove intermediate clip
                    try:
                        os.remove(clip_path)
                    except:
                        pass
                    clips.append(final_clip_path)
                    logger.info(f"Created clip: {final_clip_path}")
                else:
                    # If subtitles fail, use clip without subtitles
                    clips.append(clip_path)
                    logger.info(f"Created clip (no subtitles): {clip_path}")

        # Mark video as processed
        self.mark_as_processed(video_path)

        return clips

# Create global instance
clipper = Clipper()

def create_clips(video_path):
    """Public function to create clips from video"""
    return clipper.process_video(video_path)