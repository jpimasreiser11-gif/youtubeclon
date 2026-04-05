"""
Adjust clip boundaries to align with natural silence points
Takes Gemini-suggested clips and refines them to end/start at detected silences
"""
import argparse
import json
from typing import List, Dict, Optional

def find_nearest_silence(
    target_time: float,
    boundary_points: List[float],
    max_distance: float = 3.0,
    direction: str = 'after'
) -> Optional[float]:
    """
    Find the nearest silence point to a target time
    
    Args:
        target_time: The time we want to adjust
        boundary_points: List of silence boundary timestamps
        max_distance: Maximum search distance in seconds
        direction: 'before' or 'after' - which direction to prefer
    
    Returns:
        Adjusted timestamp, or None if no suitable silence found
    """
    if not boundary_points:
        return None
    
    # Filter points within max_distance
    candidates = []
    for point in boundary_points:
        distance = abs(point - target_time)
        if distance <= max_distance:
            candidates.append((point, distance))
    
    if not candidates:
        return None
    
    # Sort by distance
    candidates.sort(key=lambda x: x[1])
    
    # If direction preference specified, filter accordingly
    if direction == 'after':
        # Prefer points after target_time
        after_points = [p for p, d in candidates if p >= target_time]
        if after_points:
            return after_points[0]
    elif direction == 'before':
        # Prefer points before target_time
        before_points = [p for p, d in candidates if p <= target_time]
        if before_points:
            return before_points[-1]
    
    # Fallback: return closest point regardless of direction
    return candidates[0][0]

def adjust_clip_boundaries(
    clips: List[Dict],
    boundary_points: List[float],
    min_duration: float = 25.0,
    max_duration: float = 65.0,
    max_search_distance: float = 3.0
) -> List[Dict]:
    """
    Adjust clip start/end times to align with silence points
    
    Args:
        clips: List of clip dicts with 'start_time', 'end_time', 'title'
        boundary_points: List of silence boundary timestamps
        min_duration: Minimum clip duration in seconds
        max_duration: Maximum clip duration in seconds
        max_search_distance: How far to search for silence points (seconds)
    
    Returns:
        Adjusted clips list
    """
    adjusted_clips = []
    
    print(f"🔧 Adjusting {len(clips)} clips to align with {len(boundary_points)} silence points")
    print(f"📏 Constraints: {min_duration}s - {max_duration}s duration")
    
    for i, clip in enumerate(clips):
        original_start = clip['start_time']
        original_end = clip['end_time']
        original_duration = original_end - original_start
        
        print(f"\n📍 Clip {i+1}: \"{clip.get('title', 'Untitled')}\"")
        print(f"  Original: {original_start:.2f}s - {original_end:.2f}s ({original_duration:.2f}s)")
        
        # Adjust end time to nearest silence AFTER the suggested end
        adjusted_end = find_nearest_silence(
            original_end,
            boundary_points,
            max_distance=max_search_distance,
            direction='after'
        )
        
        # Adjust start time to nearest silence BEFORE the suggested start
        adjusted_start = find_nearest_silence(
            original_start,
            boundary_points,
            max_distance=max_search_distance,
            direction='before'
        )
        
        # Use adjusted times, fallback to original if no silence found
        start_time = adjusted_start if adjusted_start is not None else original_start
        end_time = adjusted_end if adjusted_end is not None else original_end
        
        # Validate duration constraints
        duration = end_time - start_time
        
        if duration < min_duration:
            # Clip too short - try extending end
            print(f"  ⚠️  Duration too short ({duration:.2f}s), extending...")
            # Find next silence point to extend to
            extended_end = find_nearest_silence(
                start_time + min_duration,
                boundary_points,
                max_distance=max_search_distance * 2,  # Search further
                direction='after'
            )
            if extended_end and (extended_end - start_time) >= min_duration:
                end_time = extended_end
            else:
                # No suitable silence, use original end + buffer
                end_time = start_time + min_duration
        
        elif duration > max_duration:
            # Clip too long - try shortening
            print(f"  ⚠️  Duration too long ({duration:.2f}s), shortening...")
            # Find earlier silence point
            shortened_end = find_nearest_silence(
                start_time + max_duration,
                boundary_points,
                max_distance=max_search_distance * 2,
                direction='before'
            )
            if shortened_end and (shortened_end - start_time) <= max_duration:
                end_time = shortened_end
            else:
                # No suitable silence, use max duration
                end_time = start_time + max_duration
        
        # Final duration check
        final_duration = end_time - start_time
        
        adjusted_clip = {
            'title': clip.get('title', f'Clip {i+1}'),
            'start_time': round(start_time, 2),
            'end_time': round(end_time, 2),
            'duration': round(final_duration, 2),
            'adjustments': {
                'start_adjusted': abs(start_time - original_start) > 0.1,
                'end_adjusted': abs(end_time - original_end) > 0.1,
                'start_delta': round(start_time - original_start, 2),
                'end_delta': round(end_time - original_end, 2)
            }
        }
        
        adjusted_clips.append(adjusted_clip)
        
        print(f"  Adjusted: {start_time:.2f}s - {end_time:.2f}s ({final_duration:.2f}s)")
        if adjusted_clip['adjustments']['start_adjusted']:
            print(f"    ✓ Start shifted by {adjusted_clip['adjustments']['start_delta']:+.2f}s")
        if adjusted_clip['adjustments']['end_adjusted']:
            print(f"    ✓ End shifted by {adjusted_clip['adjustments']['end_delta']:+.2f}s")
    
    print(f"\n✅ Adjusted {len(adjusted_clips)} clips")
    return adjusted_clips

def main():
    parser = argparse.ArgumentParser(description="Adjust clip boundaries to silence points")
    parser.add_argument('--clips', required=True, help='Input JSON with clip suggestions')
    parser.add_argument('--silences', required=True, help='Input JSON with silence data')
    parser.add_argument('--output', help='Output JSON file (default: <clips>_adjusted.json)')
    parser.add_argument('--min-duration', type=float, default=25.0, help='Min clip duration (seconds)')
    parser.add_argument('--max-duration', type=float, default=65.0, help='Max clip duration (seconds)')
    parser.add_argument('--max-search', type=float, default=3.0, help='Max search distance for silences (seconds)')
    
    args = parser.parse_args()
    
    # Load clips
    print(f"📂 Loading clips from: {args.clips}")
    with open(args.clips, 'r', encoding='utf-8') as f:
        clips_data = json.load(f)
    
    # Handle different input formats
    if isinstance(clips_data, list):
        clips = clips_data
    elif 'clips' in clips_data:
        clips = clips_data['clips']
    else:
        raise ValueError("Invalid clips JSON format")
    
    # Load silences
    print(f"📂 Loading silences from: {args.silences}")
    with open(args.silences, 'r', encoding='utf-8') as f:
        silence_data = json.load(f)
    
    boundary_points = silence_data.get('boundary_points', [])
    
    if not boundary_points:
        print("⚠️  Warning: No boundary points found in silence data")
        print("Clips will not be adjusted")
        boundary_points = []
    
    # Adjust clips
    adjusted_clips = adjust_clip_boundaries(
        clips,
        boundary_points,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
        max_search_distance=args.max_search
    )
    
    # Prepare output
    output_data = {
        'clips': adjusted_clips,
        'total_clips': len(adjusted_clips),
        'metadata': {
            'min_duration': args.min_duration,
            'max_duration': args.max_duration,
            'max_search_distance': args.max_search,
            'boundary_points_used': len(boundary_points)
        }
    }
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = args.clips.replace('.json', '_adjusted.json')
    
    # Write JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n💾 Saved adjusted clips to: {output_path}")
    
    return 0

if __name__ == '__main__':
    exit(main())
