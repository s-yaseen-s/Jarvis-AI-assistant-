from fury import create_tool

_oq = None

def set_output_queue(q):
    global _oq
    _oq = q

def private_mode_tool():
    def set_private_mode(enabled: bool):
        if _oq:
            _oq.put({"type": "private_mode", "enabled": enabled})
        if enabled:
            return {"success": True, "message": "Private mode enabled. Audio input suspended."}
        return {"success": True, "message": "Private mode disabled. Resuming audio monitoring."}

    return create_tool(
        id="set_private_mode",
        description=(
            "Enable or disable private mode. "
            "When enabled, JARVIS completely stops listening to audio input. "
            "Use when user says 'private mode', 'stop listening', 'go private'. "
            "Disable when user says 'resume', 'I'm back', 'disable private mode'."
        ),
        execute=set_private_mode,
        input_schema={
            "type": "object",
            "properties": {
                "enabled": {"type": "boolean", "description": "True to enable private mode, False to disable"},
            },
            "required": ["enabled"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
            },
            "required": ["success"],
        },
    )
