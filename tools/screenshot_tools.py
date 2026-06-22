"""Screenshot capture tools for J.A.R.V.I.S.

Provides screenshot capture with optional AI vision analysis.
Screenshots are saved to the screenshots/ directory.
"""

import os
import base64
import io
from datetime import datetime
from pathlib import Path
from fury import create_tool

SCREENSHOTS_DIR = Path("screenshots")


def screenshot_tool():
    """Create a tool for capturing screenshots.
    
    Supports saving screenshots to disk and optionally analyzing them
    with vision AI to describe what's on the screen.
    
    Returns:
        Fury tool object for taking screenshots
    """
    def take_screenshot(filename: str = "", analyze: bool = False):
        """Capture a screenshot and optionally analyze it with AI vision.
        
        Args:
            filename: Optional custom filename (without path). Auto-generated if not provided
            analyze: If True, use GPT-4o-mini vision to describe the screenshot
            
        Returns:
            Dict with success status, file path, size, and optional description
        """
        try:
            from PIL import ImageGrab
            SCREENSHOTS_DIR.mkdir(exist_ok=True)
            name = filename or f"jarvis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            if not name.endswith(".png"):
                name += ".png"
            path = SCREENSHOTS_DIR / name
            img = ImageGrab.grab()
            img.save(str(path))
            result = {
                "success": True,
                "path": str(path),
                "size": f"{img.width}x{img.height}",
            }
            # Optionally analyze with vision
            if analyze:
                try:
                    import httpx
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode()
                    api_key = os.getenv("OPENAI_API_KEY", "")
                    resp = httpx.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={
                            "model": "gpt-4o-mini",
                            "max_tokens": 512,
                            "messages": [{
                                "role": "user",
                                "content": [
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                                    {"type": "text", "text": "Describe what is on this screen briefly."},
                                ],
                            }],
                        },
                        timeout=30,
                    )
                    resp.raise_for_status()
                    result["description"] = resp.json()["choices"][0]["message"]["content"]
                except Exception as e:
                    result["vision_error"] = str(e)
            return result
        except ImportError:
            return {"error": "Pillow not installed — run: pip install Pillow"}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="take_screenshot",
        description="Take a screenshot and save it. Set analyze=True to also get an AI vision description of what's on screen.",
        execute=take_screenshot,
        input_schema={
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Optional filename"},
                "analyze":  {"type": "boolean", "description": "If true, use AI vision to describe the screenshot"},
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success":     {"type": "boolean"},
                "path":        {"type": "string"},
                "size":        {"type": "string"},
                "description": {"type": "string"},
            },
            "required": [],
        },
    )