"""Private mode control tool for J.A.R.V.I.S.

Provides user privacy control by disabling audio input when requested.
Private mode completely stops listening to microphone input.
"""

from fury import create_tool

_oq = None


def set_output_queue(q):
    """Register the output queue for private mode notifications.
    
    This queue receives messages about private mode state changes.
    
    Args:
        q: Queue object for sending private mode commands
    """
    global _oq
    _oq = q


def private_mode_tool():
    """Create a tool for toggling private mode.
    
    When enabled, J.A.R.V.I.S. stops listening to audio input completely,
    giving the user full privacy. Useful when discussing sensitive topics
    or when the user needs uninterrupted time.
    
    Returns:
        Fury tool object for controlling private mode
    """
    def set_private_mode(enabled: bool):
        """Enable or disable private mode.
        
        When enabled, completely stops audio input monitoring.
        User can resume by disabling private mode.
        
        Args:
            enabled: True to enable private mode (stop listening),
                    False to disable and resume audio monitoring
            
        Returns:
            Dict with success status and status message
        """
        if _oq:
            _oq.put({"type": "private_mode", "enabled": enabled})
        if enabled:
            return {"success": True, "message": "Private mode enabled. Audio input suspended."}
        return {"success": True, "message": "Private mode disabled. Resuming audio monitoring."}

    return create_tool(
        id="set_private_mode",
        description=(
            "Enable or disable private mode. "
            "When enabled, J.A.R.V.I.S. completely stops listening to audio input. "
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