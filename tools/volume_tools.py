from fury import create_tool


def volume_tool():
    def control_volume(action: str, level: int = 50):
        """
        action: 'set' | 'up' | 'down' | 'mute' | 'unmute' | 'get'
        level: 0-100 (used with 'set')
        Uses Windows Core Audio via pycaw.
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
