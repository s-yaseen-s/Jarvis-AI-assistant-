"""Keyboard and mouse automation tools via pyautogui."""

import time
from fury import create_tool


def press_hotkey_tool():
    def press_hotkey(keys: str):
        """keys: comma-separated, e.g. 'ctrl,c' or 'win,d'"""
        try:
            import pyautogui
            parts = [k.strip() for k in keys.split(",")]
            pyautogui.hotkey(*parts)
            return {"success": True, "keys": keys}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="press_hotkey",
        description=(
            "Press a keyboard shortcut. "
            "Pass keys as comma-separated: e.g. 'ctrl,c' to copy, 'win,d' for desktop, "
            "'alt,f4' to close, 'ctrl,alt,t' to open terminal."
        ),
        execute=press_hotkey,
        input_schema={
            "type": "object",
            "properties": {
                "keys": {"type": "string",
                         "description": "Comma-separated key names, e.g. 'ctrl,c'"},
            },
            "required": ["keys"],
        },
        output_schema={
            "type": "object",
            "properties": {"success": {"type": "boolean"}, "keys": {"type": "string"}},
            "required": [],
        },
    )


def type_text_tool():
    def type_text(text: str, delay_ms: int = 25):
        try:
            import pyautogui
            time.sleep(0.3)  # brief pause so focus settles
            pyautogui.typewrite(text, interval=delay_ms / 1000)
            return {"success": True, "typed": len(text)}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="type_text",
        description="Type text as keyboard input into the currently focused window",
        execute=type_text,
        input_schema={
            "type": "object",
            "properties": {
                "text":     {"type": "string", "description": "Text to type"},
                "delay_ms": {"type": "integer",
                             "description": "Delay between keystrokes in ms (default 25)"},
            },
            "required": ["text"],
        },
        output_schema={
            "type": "object",
            "properties": {"success": {"type": "boolean"}, "typed": {"type": "integer"}},
            "required": [],
        },
    )


def mouse_click_tool():
    def mouse_click(x: int, y: int, button: str = "left", clicks: int = 1):
        try:
            import pyautogui
            pyautogui.click(x, y, clicks=clicks, button=button)
            return {"success": True, "x": x, "y": y, "button": button}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="mouse_click",
        description="Click the mouse at screen coordinates (x, y)",
        execute=mouse_click,
        input_schema={
            "type": "object",
            "properties": {
                "x":       {"type": "integer", "description": "X screen coordinate"},
                "y":       {"type": "integer", "description": "Y screen coordinate"},
                "button":  {"type": "string", "enum": ["left", "right", "middle"],
                            "description": "Mouse button (default: left)"},
                "clicks":  {"type": "integer", "description": "Number of clicks (default 1)"},
            },
            "required": ["x", "y"],
        },
        output_schema={
            "type": "object",
            "properties": {"success": {"type": "boolean"}},
            "required": [],
        },
    )
