import os
import json
from dotenv import load_dotenv

load_dotenv()

# Test with the OLD SDK method (google.generativeai) instead of google.genai
def test_gemini_old_sdk():
    import google.generativeai as genai
    
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"Testing with API key: {api_key[:10]}...{api_key[-5:]}")
    
    genai.configure(api_key=api_key)
    
    # Simple test transcript
    test_transcript = [
        {"text": "Hello, this is a test video.", "start": 0, "end": 5},
        {"text": "We're testing clip generation.", "start": 5, "end": 10},
        {"text": "This should generate multiple clips.", "start": 10, "end": 15},
    ]
    
    prompt = f"""
    You are a Viral Content Expert.
    Analyze the following video transcript and identify the most viral segments.
    
    Transcript JSON:
    {json.dumps(test_transcript)}
    
    Rules:
    1. Identify roughly 10 highly viral clips.
    2. For each clip return: 'start' (float), 'end' (float), 'score' (0-100), 'title', 'reason'.
    3. Output strictly valid JSON list of objects. No markdown formatting.
    """
    
    print("\nSending request to Gemini using OLD SDK...")
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        
        print("\n=== SUCCESS! RAW RESPONSE ===")
        print(response.text[:500])
        print("\n=== Parsing JSON ===")
        
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        
        text = text.strip()
        clips = json.loads(text)
        print(f"\n✅ Successfully parsed {len(clips)} clips!")
        for i, clip in enumerate(clips[:3], 1):  # Show first 3
            print(f"  {i}. {clip.get('title', 'N/A')} ({clip.get('start', 0)}-{clip.get('end', 0)}s)")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"Error type: {type(e).__name__}")

if __name__ == "__main__":
    test_gemini_old_sdk()
