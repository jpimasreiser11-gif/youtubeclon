import google.generativeai as genai
import os
import json
import argparse
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

class SocialDistributor:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')

    def generate_viral_metadata(self, transcript):
        """Generate high-impact titles and descriptions for social media"""
        prompt = f"""
        ACT AS: Expert Social Media Manager (TikTok/Reels/Shorts).
        TASK: Generate viral metadata for a video based on this transcript.
        
        TRANSCRIPT:
        "{transcript}"
        
        RETURN ONLY JSON:
        {{
          "title": "Un Título que Obligue a Hacer Click (Máx 50 chars)",
          "description": "Una descripción corta con 3-5 hashtags virales.",
          "hook_score": 95,
          "target_audience": "Entrepreneurship / Tech / General"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            import re
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except Exception as e:
            print(f"❌ Metadata generation failed: {e}")
        return None

    def prepare_bundle(self, video_path, metadata, output_dir):
        """Prepare a bundle for manual or automated upload"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        bundle_id = os.path.basename(video_path).split('.')[0]
        meta_path = os.path.join(output_dir, f"{bundle_id}_meta.json")
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
            
        print(f"📦 Bundle ready: {video_path} + {meta_path}")
        return meta_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True)
    parser.add_argument("--transcript", required=True)
    parser.add_argument("--output", default="bundles/")
    
    args = parser.parse_args()
    
    distributor = SocialDistributor()
    print(f"🚀 Generating viral metadata for: {args.video}")
    
    metadata = distributor.generate_viral_metadata(args.transcript)
    if metadata:
        distributor.prepare_bundle(args.video, metadata, args.output)
        print("✅ Social Distribution Metadata Generated.")
    else:
        print("❌ Failed to generate metadata.")
