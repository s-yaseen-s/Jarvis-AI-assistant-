"""Clipboard access tools for J.A.R.V.I.S.

Provides tools for reading from and writing to the system clipboard.
Uses pyperclip for cross-platform clipboard access.
"""

from fury import create_tool


def get_clipboard_tool():
    """Create a tool for reading clipboard contents.
    
    Returns:
        Fury tool object for reading clipboard
    """
    def get_clipboard():
        """Read the current contents of the system clipboard.
        
        Returns:
            Dict with clipboard content and text length
        """
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
    """Create a tool for writing to the clipboard.
    
    Returns:
        Fury tool object for writing to clipboard
    """
    def set_clipboard(text: str):
        """Write text to the system clipboard.
        
        Args:
            text: Text to copy to clipboard
            
        Returns:
            Dict with success status and text length
        """
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