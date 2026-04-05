import os
import requests
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_keywords_from_transcript(text):
    """Use Gemini to extract key visual themes from transcript"""
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    prompt = f"""
    Analiza este texto y extrae 3 conceptos visuales clave que representarían bien el contenido como clips de b-roll (video de stock).
    Responde solo con los conceptos en inglés, separados por comas.
    Texto: {text}
    """
    try:
        response = model.generate_content(prompt)
        keywords = [k.strip() for k in response.text.split(",")]
        return keywords
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return ["business", "nature", "technology"] # Fallbacks

def search_pexels_video(query):
    """Search Pexels for a short video clip"""
    if not PEXELS_API_KEY:
        print("PEXELS_API_KEY not found in .env")
        return None
        
    url = f"https://api.pexels.com/videos/search?query={query}&per_page=1&orientation=portrait"
    headers = {"Authorization": PEXELS_API_KEY}
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if data.get("videos") and len(data["videos"]) > 0:
            video_files = data["videos"][0].get("video_files")
            if not video_files:
                return None
            # Prefer 1080x1920 if available, else first one
            best_file = next((f for f in video_files if f["width"] == 1080), video_files[0])
            return best_file["link"]
    except Exception as e:
        print(f"Pexels search error: {e}")
    return None

def download_broll(url, output_path):
    try:
        response = requests.get(url, stream=True)
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        return True
    except Exception as e:
        print(f"Download error: {e}")
        return False

def get_broll_for_clip(transcript_text, project_id, clip_index):
    """Main entry point to get a B-roll clip for a segment"""
    keywords = get_keywords_from_transcript(transcript_text)
    print(f"Keywords for B-Roll: {keywords}")
    
    output_dir = os.path.join("data", "broll", project_id)
    os.makedirs(output_dir, exist_ok=True)
    
    for kw in keywords:
        video_url = search_pexels_video(kw)
        if video_url:
            output_path = os.path.join(output_dir, f"broll_{clip_index}_{kw.replace(' ', '_')}.mp4")
            if download_broll(video_url, output_path):
                print(f"Downloaded B-roll: {output_path}")
                return output_path
    
    return None

if __name__ == "__main__":
    # Test
    test_text = "I was struggling with my startup until I discovered this hidden productivity hack."
    res = get_broll_for_clip(test_text, "test_proj", 0)
    print(f"Result: {res}")
