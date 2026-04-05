import os
import sys

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.media_engine.video_composer import VideoComposer

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    composer = VideoComposer(output_dir=os.path.join(project_root, "assets", "renders"))
    
    # Paths
    voice_path = os.path.join(project_root, "assets", "test_mystery.mp3")
    image_paths = [os.path.join(project_root, "assets", "test_assets", "mystery_castle.jpg")]
    # We could also use a dummy music file or none for this test
    # Let's try to render without music first to verify visuals
    
    print("Starting V2 Integration Test...")
    if not os.path.exists(voice_path):
        print(f"Error: Voice file {voice_path} not found. Generate it first with tts_engine.py")
        return
        
    try:
        scene_file = composer.render_scene_with_effects(
            voice_path=voice_path,
            image_paths=image_paths,
            scene_id="v2_test"
        )
        print(f"Success! Scene rendered at: {scene_file}")
    except Exception as e:
        print(f"Integration Test Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
