"""
Neural Audio Pro - Normalizes audio to professional broadcast standards
Using FFmpeg's loudnorm filter for dynamic audio normalization
"""
import argparse
import subprocess
import json
import sys
from pathlib import Path

FFMPEG_PATH = r"ffmpeg"

def analyze_loudness(input_file):
    """Analyze current loudness levels of audio"""
    cmd = [
        FFMPEG_PATH,
        '-i', str(input_file),
        '-af', 'loudnorm=print_format=json',
        '-f', 'null',
        '-'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)
    
    # Extract JSON from output
    output_lines = result.stdout.split('\n')
    json_start = False
    json_lines = []
    
    for line in output_lines:
        if '[Parsed_loudnorm' in line:
            json_start = True
            continue
        if json_start:
            if line.strip().startswith('{'):
                json_lines.append(line)
            elif line.strip().startswith('}'):
                json_lines.append(line)
                break
            elif json_lines:
                json_lines.append(line)
    
    if json_lines:
        try:
            stats = json.loads(''.join(json_lines))
            return stats
        except json.JSONDecodeError:
            pass
    
    return None

def normalize_audio_pro(input_file, output_file, target_lufs=-14, target_tp=-1, target_lra=11):
    """
    Normalize audio to professional broadcast standards
    
    Args:
        input_file: Input video file
        output_file: Output video file
        target_lufs: Target integrated loudness (-14 LUFS for social media)
        target_tp: Target true peak (-1 dB to prevent clipping)
        target_lra: Target loudness range (11 LU is standard)
    """
    print(f"📊 Analyzing audio levels...")
    
    # First pass: analyze
    stats = analyze_loudness(input_file)
    
    if stats:
        print(f"  Current I: {stats.get('input_i', 'N/A')} LUFS")
        print(f"  Current TP: {stats.get('input_tp', 'N/A')} dB")
        print(f"  Current LRA: {stats.get('input_lra', 'N/A')} LU")
    
    # Second pass: normalize with measured parameters
    print(f"🎵 Normalizing audio to {target_lufs} LUFS...")
    
    if stats:
        # Use two-pass loudnorm for better quality
        measured_i = stats.get('input_i', target_lufs)
        measured_tp = stats.get('input_tp', target_tp)
        measured_lra = stats.get('input_lra', target_lra)
        measured_thresh = stats.get('input_thresh', -70)
        
        loudnorm_filter = f"loudnorm=I={target_lufs}:TP={target_tp}:LRA={target_lra}:measured_I={measured_i}:measured_TP={measured_tp}:measured_LRA={measured_lra}:measured_thresh={measured_thresh}:linear=true:print_format=summary"
    else:
        # Single-pass if analysis failed
        loudnorm_filter = f"loudnorm=I={target_lufs}:TP={target_tp}:LRA={target_lra}:print_format=summary"
    
    cmd = [
        FFMPEG_PATH,
        '-i', str(input_file),
        '-af', loudnorm_filter,
        '-c:v', 'copy',  # Copy video stream without re-encoding
        '-c:a', 'aac',   # Re-encode audio
        '-b:a', '192k',  # High quality audio bitrate
        '-y',  # Overwrite output
        str(output_file)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ Audio normalization complete!")
        
        # Extract final stats from output
        if 'Parsed_loudnorm' in result.stderr:
            print("\n📊 Final stats:")
            for line in result.stderr.split('\n'):
                if 'Output Integrated' in line or 'Output True Peak' in line or 'Output LRA' in line:
                    print(f"  {line.strip()}")
        
        return {
            'success': True,
            'output': str(output_file),
            'target_lufs': target_lufs,
            'stats': stats
        }
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during normalization: {e}")
        print(f"stderr: {e.stderr}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    parser = argparse.ArgumentParser(description="Neural Audio Pro - Professional audio normalization")
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--output', required=True, help='Output video file')
    parser.add_argument('--target-lufs', type=float, default=-14, help='Target LUFS (default: -14)')
    parser.add_argument('--target-tp', type=float, default=-1, help='Target true peak in dB (default: -1)')
    parser.add_argument('--target-lra', type=float, default=11, help='Target loudness range (default: 11)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        sys.exit(1)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    result = normalize_audio_pro(
        input_path,
        output_path,
        target_lufs=args.target_lufs,
        target_tp=args.target_tp,
        target_lra=args.target_lra
    )
    
    # Output JSON result
    print(json.dumps(result))
    
    if not result['success']:
        sys.exit(1)

if __name__ == '__main__':
    main()
