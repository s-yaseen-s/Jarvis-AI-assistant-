"""Clipboard read/write tools."""

from fury import create_tool


def get_clipboard_tool():
    def get_clipboard():
        try:
            import pyperclip
            text = pyperclip.paste()
            return {"content": text, "length": len(text)}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="get_clipboard",
        description="Read the current contents of the clipboard",
        execute=get_clipboard,
        input_schema={"type": "object", "properties": {}, "required": []},
        output_schema={
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "length":  {"type": "integer"},
            },
            "required": [],
        },
    )


def set_clipboard_tool():
    def set_clipboard(text: str):
        try:
            import pyperclip
            pyperclip.copy(text)
            return {"success": True, "length": len(text)}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="set_clipboard",
        description="Write text to the clipboard",
        execute=set_clipboard,
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to copy to clipboard"},
            },
            "required": ["text"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "length":  {"type": "integer"},
            },
            "required": [],
        },
    )
