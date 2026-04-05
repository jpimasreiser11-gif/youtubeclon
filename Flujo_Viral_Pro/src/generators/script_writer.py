import google.generativeai as genai
import os
import json
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add project root path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.utils.db_manager import update_video_script, get_video_by_id

def generate_script(video_id):
    # Load API Key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment")
        return False

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash')

    # Get video info
    video = get_video_by_id(video_id)
    if not video:
        print(f"Error: Video ID {video_id} not found")
        return False

    print(f"Generating script for: {video.topic} ({video.niche})")

    # Get Tone Rules from channel folder
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    tone_rules = ""
    # Search for niche folder (e.g., Mystery -> Channel-Mystery)
    channel_folder = f"Channel-{video.niche.capitalize()}"
    rules_path = os.path.join(project_root, channel_folder, ".agent", "rules", "tone.md")
    
    if os.path.exists(rules_path):
        with open(rules_path, "r", encoding="utf-8") as f:
            tone_rules = f.read()
            print(f"Loaded tone rules for {video.niche}")
    else:
        print(f"Warning: Tone rules not found at {rules_path}. Using default.")

    prompt = f"""
    Act as a professional viral storytelling architect.
    Create a highly engaging DOCUMENTARY script for a long-form video (10-15 minutes) regarding: "{video.topic}"
    Niche: {video.niche}

    CHANNEL SPECIFIC TONE RULES:
    {tone_rules}

    STRUCTURE REQUIREMENTS (The Triple H Pattern):
    1. HOOK (00:00 - 01:00): Capture immediate interest. NO intros. Start in media res.
    2. HEIGHTEN (01:00 - 10:00): Build tension/interest. Reveal a new "Plot Twist" or revelation every 200 words.
    3. HOLD (10:00 - 15:00): Lead to a dramatic climax and a perspective-shifting resolution.

    WORD COUNT TARGET: Approximately 2,500 words.

    Return ONLY a JSON object with this format:
    {{
        "title": "Dramatic Documental Title",
        "hook": "Full hook text...",
        "body": "Full body segments with [Visual Instructions]...",
        "climax": "The final revelation...",
        "cta": "Channel-specific CTA...",
        "visual_keywords": ["mystery", "dark", "castle", "cinematic"],
        "bg_music_style": "Dramatic Drone / Orchestral Tension"
    }}
    """

    import time

    def safe_generate(prompt_text):
        max_retries = 5
        base_delay = 20
        for attempt in range(max_retries):
            try:
                response = model.generate_content(prompt_text)
                return response.text
            except Exception as e:
                print(f"Gemini Error en intento {attempt + 1}: {e}")
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)
                        print(f"Rate limit hit. Esperando {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                raise e

    print(f"Generating Long-Form script via Chunking for: {video.topic}")
    
    # 1. Generate HOOK
    print("Generating Hook...")
    hook_prompt = f"{prompt}\n\nACTION: Generate ONLY the 'hook' section (approx 300 words). Follow Tone Rules: {tone_rules}"
    hook_text = safe_generate(hook_prompt)
    
    time.sleep(15) # Breathing room
    
    # 2. Generate BODY (PART 1 - HEIGHTEN)
    print("Generating Body (Heighten)...")
    body_prompt = f"{prompt}\n\nCONTEXT: Hook is done. \nACTION: Generate the first half of the 'body' (approx 1000 words). Build tension. \nRULES: {tone_rules}"
    body1_text = safe_generate(body_prompt)
    
    time.sleep(15)
    
    # 3. Generate BODY (PART 2 - HOLD)
    print("Generating Body (Climax preparation)...")
    body2_prompt = f"{prompt}\n\nCONTEXT: Previous sections ready. \nACTION: Generate the second half of the 'body' and the 'climax' (approx 1000 words). \nRULES: {tone_rules}"
    body2_text = safe_generate(body2_prompt)

    # 4. Final Assembly
    final_script = {
        "title": f"The Mystery of {video.topic}",
        "hook": hook_text,
        "body": body1_text + "\n\n" + body2_text,
        "cta": f"Discover more {video.niche} secrets. Subscribe.",
        "visual_keywords": ["mystery", "cinematic", "documentary"],
        "bg_music_style": "Dramatic Tension"
    }

    try:
        script_json_str = json.dumps(final_script, indent=4)
        # Save to DB
        update_video_script(video_id, script_json_str)
        print(f"Long-Form Script (v2) assembled and saved for Video ID {video_id}")
        return True
    except Exception as e:
        print(f"Error assembling script: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_writer.py <video_id>")
        sys.exit(1)
    
    video_id = int(sys.argv[1])
    generate_script(video_id)
