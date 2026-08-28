import time
from pathlib import Path
from PIL import Image
import mss
import mss.tools
import config
from google import genai
from google.genai import types

def capture_screen() -> Path:
    """Captures the current desktop screen and returns the file path."""
    timestamp = int(time.time())
    file_path = config.SCREENSHOTS_DIR / f"screen_vision_{timestamp}.png"
    
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        sct_img = sct.grab(monitor)
        mss.tools.to_png(sct_img.rgb, sct_img.size, output=str(file_path))
    
    return file_path


def analyze_screen_with_gemini(user_query: str = "Describe what is on my screen and highlight key information.") -> str:
    """Captures desktop screen and analyzes it using Gemini Multimodal Vision."""
    api_key = config.GEMINI_API_KEY
    if not api_key:
        return "Gemini API key is not configured. Please add your GEMINI_API_KEY to settings."

    try:
        # 1. Capture screen
        img_path = capture_screen()
        img = Image.open(img_path)

        # 2. Initialize Gemini Client
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are Nova Pro, an advanced desktop AI assistant with direct screen vision.
The user asked: "{user_query}"

Look carefully at the user's desktop screenshot provided:
- Provide a clear, concise, and helpful response.
- If there's an error, explain the cause and how to fix it.
- If it's a document/webpage, summarize the salient points.
- Keep the response direct and voice-friendly (avoid markdown overload or huge code dumps unless asked).
"""
        response = client.models.generate_content(
            model=config.DEFAULT_MODEL,
            contents=[img, prompt]
        )
        return response.text
    except Exception as e:
        return f"Error analyzing screen: {e}"
