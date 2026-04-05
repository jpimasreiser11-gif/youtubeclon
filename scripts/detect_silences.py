"""
Detect silence segments in audio files
Uses pydub for audio analysis and outputs silence timestamps in JSON format
"""
import argparse
import json
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import detect_silence
import os

def detect_audio_silences(
    audio_path: str,
    min_silence_len: int = 500,  # milliseconds
    silence_thresh: int = -40,    # dB
    seek_step: int = 10           # milliseconds (precision)
):
    """
    Detect silence segments in an audio file
    
    Args:
        audio_path: Path to audio file (mp3, wav, etc.)
        min_silence_len: Minimum length of silence to detect (ms)
        silence_thresh: Silence threshold in dB (lower = more sensitive)
        seek_step: Step size for analysis (lower = more precise but slower)
    
    Returns:
        List of silence segments as {'start': float, 'end': float} in seconds
    """
    print(f"🎵 Loading audio: {audio_path}")
    
    # Load audio file
    audio = AudioSegment.from_file(audio_path)
    duration_sec = len(audio) / 1000.0
    
    print(f"📊 Audio duration: {duration_sec:.2f}s")
    print(f"🔍 Detecting silences (threshold: {silence_thresh}dB, min: {min_silence_len}ms)...")
    
    # Detect silence segments
    silence_ranges = detect_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        seek_step=seek_step
    )
    
    # Convert from milliseconds to seconds
    silences = []
    for start_ms, end_ms in silence_ranges:
        silences.append({
            'start': start_ms / 1000.0,
            'end': end_ms / 1000.0,
            'duration': (end_ms - start_ms) / 1000.0
        })
    
    print(f"✅ Found {len(silences)} silence segments")
    
    # Print summary
    if silences:
        total_silence = sum(s['duration'] for s in silences)
        print(f"📈 Total silence: {total_silence:.2f}s ({total_silence/duration_sec*100:.1f}% of audio)")
        
        # Show first few silences
        print("\n🔸 First few silence points:")
        for i, s in enumerate(silences[:5]):
            print(f"  {i+1}. {s['start']:.2f}s - {s['end']:.2f}s ({s['duration']:.2f}s)")
        if len(silences) > 5:
            print(f"  ... and {len(silences) - 5} more")
    
    return silences

def get_silence_boundary_points(silences: list) -> list:
    """
    Extract key boundary points (end of each silence) for clip cutting
    
    Args:
        silences: List of silence segments
    
    Returns:
        List of timestamps (seconds) representing good cut points
    """
    # Use the end of each silence as a natural boundary
    # (i.e., the moment speech resumes after a pause)
    boundaries = [s['end'] for s in silences]
    
    # Also include the start of the first silence (if it exists)
    if silences and silences[0]['start'] > 0:
        boundaries.insert(0, silences[0]['start'])
    
    return sorted(boundaries)

def main():
    parser = argparse.ArgumentParser(description="Detect silence in audio files")
    parser.add_argument('--audio', required=True, help='Path to audio file')
    parser.add_argument('--output', help='Output JSON file (default: <audio>_silences.json)')
    parser.add_argument('--min-silence', type=int, default=500, help='Minimum silence length in ms (default: 500)')
    parser.add_argument('--threshold', type=int, default=-40, help='Silence threshold in dB (default: -40)')
    parser.add_argument('--seek-step', type=int, default=10, help='Seek step in ms (default: 10)')
    parser.add_argument('--boundaries-only', action='store_true', help='Output only boundary points, not full silence ranges')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.audio):
        print(f"❌ Error: Audio file not found: {args.audio}")
        return 1
    
    # Detect silences
    silences = detect_audio_silences(
        args.audio,
        min_silence_len=args.min_silence,
        silence_thresh=args.threshold,
        seek_step=args.seek_step
    )
    
    # Prepare output
    if args.boundaries_only:
        output_data = {
            'audio_file': args.audio,
            'boundary_points': get_silence_boundary_points(silences),
            'total_boundaries': len(get_silence_boundary_points(silences))
        }
    else:
        output_data = {
            'audio_file': args.audio,
            'silences': silences,
            'total_silences': len(silences),
            'boundary_points': get_silence_boundary_points(silences)
        }
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        audio_stem = Path(args.audio).stem
        output_path = f"data/{audio_stem}_silences.json"
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    
    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n💾 Saved to: {output_path}")
    
    return 0

if __name__ == '__main__':
    exit(main())
