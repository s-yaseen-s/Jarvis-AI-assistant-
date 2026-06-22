"""Volume Control Tools for J.A.R.V.I.S.

Provides system volume control via Windows Core Audio API.
Supports getting, setting, muting/unmuting, and adjusting volume.
"""

from fury import create_tool


def volume_tool():
    """Create a tool for controlling system volume.
    
    Uses Windows Core Audio API via pycaw library.
    Supports get, set, up, down, mute, and unmute actions.
    
    Returns:
        Fury tool object for volume control
    """
    def control_volume(action: str, level: int = 50):
        """Control system volume using Windows Core Audio.
        
        Args:
            action: Volume action to perform:
                - 'get': Get current volume and mute status
                - 'set': Set volume to specific level (0-100)
                - 'up': Increase volume by 10%
                - 'down': Decrease volume by 10%
                - 'mute': Mute audio
                - 'unmute': Unmute audio
            level: Volume level 0-100 (only used with 'set' action)
            
        Returns:
            Dict with volume status, success flag, and error if any
        """
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices    = AudioUtilities.GetSpeakers()
            interface  = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            vol_ctrl   = cast(interface, POINTER(IAudioEndpointVolume))
            current_scalar = vol_ctrl.GetMasterVolumeLevelScalar()
            current_pct    = int(current_scalar * 100)

            if action == "get":
                muted = vol_ctrl.GetMute()
                return {"current_volume": current_pct, "muted": bool(muted)}
            elif action == "set":
                vol_ctrl.SetMasterVolumeLevelScalar(max(0.0, min(1.0, level / 100)), None)
                return {"success": True, "volume": level}
            elif action == "up":
                new = min(100, current_pct + 10)
                vol_ctrl.SetMasterVolumeLevelScalar(new / 100, None)
                return {"success": True, "volume": new}
            elif action == "down":
                new = max(0, current_pct - 10)
                vol_ctrl.SetMasterVolumeLevelScalar(new / 100, None)
                return {"success": True, "volume": new}
            elif action == "mute":
                vol_ctrl.SetMute(1, None)
                return {"success": True, "muted": True}
            elif action == "unmute":
                vol_ctrl.SetMute(0, None)
                return {"success": True, "muted": False}
            return {"error": f"Unknown action: {action}"}
        except ImportError:
            return {"error": "pycaw not installed — run: pip install pycaw"}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="control_volume",
        description="Control system volume: get, set (0-100), up, down, mute, unmute",
        execute=control_volume,
        input_schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get", "set", "up", "down", "mute", "unmute"],
                    "description": "Volume action to perform",
                },
                "level": {
                    "type": "integer",
                    "description": "Volume level 0-100 (only used with 'set')",
                },
            },
            "required": ["action"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success":        {"type": "boolean"},
                "volume":         {"type": "integer"},
                "muted":          {"type": "boolean"},
                "current_volume": {"type": "integer"},
            },
            "required": [],
        },
    )