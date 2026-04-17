
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY")
print(f"Using key: {key[:10]}...")

try:
    client = genai.Client(api_key=key)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Hello, just a test.",
    )
    print("✅ Success!")
    print(response.text)
except Exception as e:
    print("❌ Failed!")
    print(e)
