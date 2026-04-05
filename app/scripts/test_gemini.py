import os
import json
from dotenv import load_dotenv

load_dotenv()

# Test the API response with GROQ
def test_gemini():
    from groq import Groq
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ No GROQ_API_KEY found.")
        return
        
    client = Groq(api_key=api_key)
    
    # Simple test transcript
    test_transcript = [
        {"text": "Hello, this is a test video.", "start": 0, "end": 5},
        {"text": "We're testing clip generation.", "start": 5, "end": 10},
        {"text": "This should generate multiple clips.", "start": 10, "end": 15},
        {"text": "Let's see how many we get back.", "start": 15, "end": 20},
    ]
    
    prompt = f"""
    You are a Viral Content Expert (Opus Clip Creative Director).
    Analyze the following video transcript and identify the most viral segments.
    
    Transcript JSON:
    {json.dumps(test_transcript)}
    
    Rules:
    1. Identify roughly 10 highly viral clips (if the content allows, otherwise as many good ones as possible).
    2. CRITICAL: Ensure each clip has a COHERENT START and END. It must make sense on its own.
       - Do not cut mid-sentence.
       - Ensure the clip delivers a complete thought or punchline.
    3. For each clip return: 'start' (float), 'end' (float), 'score' (0-100), 'title', 'reason'.
    4. Output strictly valid JSON list of objects. No markdown formatting.
    """
    
    print("Sending request to Groq API (llama-3.3-70b-versatile)...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    
    print("\n=== RAW RESPONSE ===")
    print(response.choices[0].message.content)
    print("\n=== ATTEMPTING TO PARSE ===")
    
    text = response.choices[0].message.content.strip()
    
    # Clean markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    
    text = text.strip()
    
    try:
        clips = json.loads(text)
        print(f"\nSuccessfully parsed {len(clips)} clips:")
        for i, clip in enumerate(clips, 1):
            print(f"  {i}. {clip.get('title', 'N/A')} ({clip.get('start', 0)}-{clip.get('end', 0)}s) Score: {clip.get('score', 0)}")
    except Exception as e:
        print(f"ERROR parsing JSON: {e}")
        print(f"Cleaned text:\n{text}")

if __name__ == "__main__":
    test_gemini()
