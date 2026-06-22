"""Screen reading tools with AI vision for J.A.R.V.I.S.

Provides screen capture and GPT-4o mini vision analysis to understand
what is currently visible on the screen, answer questions about it,
and extract information from the UI.
"""

import base64
import io
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from fury import create_tool

SCREENSHOTS_DIR = Path("screenshots")


def _capture_b64() -> tuple[str, int, int]:
    """Take screenshot and return (base64_png, width, height).
    
    Returns:
        Tuple of (base64_encoded_png, width_px, height_px)
    """
    from PIL import ImageGrab
    img = ImageGrab.grab()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return b64, img.width, img.height


def _vision_describe(b64_png: str, question: str, api_key: str) -> str:
    """Send screenshot to GPT-4o mini vision and return description.
    
    Args:
        b64_png: Base64-encoded PNG image data
        question: Question or prompt to ask about the image
        api_key: OpenAI API key
        
    Returns:
        Text description/answer from vision model
    """
    import httpx
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o-mini",
            "max_tokens": 1024,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{b64_png}", "detail": "high"},
                    },
                    {"type": "text", "text": question},
                ],
            }],
        },
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def read_screen_tool():
    """Create a tool for reading and understanding screen content via AI vision.
    
    Uses GPT-4o mini vision to analyze screenshots and answer questions
    about what is visible on the screen.
    
    Returns:
        Fury tool object for screen reading
    """
    def read_screen(question: str = "Describe everything visible on the screen in detail. Include all text, UI elements, open applications, and what the user is currently doing."):
        """Capture the screen and use AI vision to understand and describe it.
        
        Args:
            question: Question or prompt to ask about the screen content.
                     Defaults to full screen description if not provided.
            
        Returns:
            Dict with success status, description from vision model, screen size, and saved path
        """
        try:
            api_key = os.getenv("OPENAI_API_KEY", "")
            b64, w, h = _capture_b64()
            # Save a copy for reference
            SCREENSHOTS_DIR.mkdir(exist_ok=True)
            img_path = SCREENSHOTS_DIR / f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            img_bytes = base64.b64decode(b64)
            img_path.write_bytes(img_bytes)
            description = _vision_describe(b64, question, api_key)
            return {
                "success": True,
                "description": description,
                "screen_size": f"{w}x{h}",
                "saved_to": str(img_path),
            }
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="read_screen",
        description=(
            "Take a screenshot and use AI vision to SEE and understand what is on the screen. "
            "Can answer specific questions about screen content: 'what app is open?', "
            "'what does the error say?', 'what is the user doing?', etc. "
            "Far more powerful than OCR — understands context, UI, images, code, everything visible."
        ),
        execute=read_screen,
        input_schema={
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "What to look for or describe on the screen (default: full description)",
                },
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success":     {"type": "boolean"},
                "description": {"type": "string"},
                "screen_size": {"type": "string"},
                "saved_to":    {"type": "string"},
            },
            "required": [],
        },
    )