from datetime import datetime
from pathlib import Path
from fury import create_tool

SCREENSHOTS_DIR = Path("screenshots")


def capture_camera_tool():
    def capture_camera(camera_index: int = 0, filename: str = ""):
        try:
            import cv2
            cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                return {"error": f"Camera {camera_index} not found or in use"}
            # let camera warm up
            for _ in range(3):
                cap.read()
            ret, frame = cap.read()
            cap.release()
            if not ret:
                return {"error": "Failed to capture frame from camera"}
            SCREENSHOTS_DIR.mkdir(exist_ok=True)
            name = filename or f"camera_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            if not name.endswith(".png"):
                name += ".png"
            path = SCREENSHOTS_DIR / name
            cv2.imwrite(str(path), frame)
            h, w = frame.shape[:2]
            return {"success": True, "path": str(path.resolve()), "size": f"{w}x{h}", "camera": camera_index}
        except ImportError:
            return {"error": "opencv-python not installed"}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="capture_camera",
        description="Capture a photo from the webcam/camera and save it to disk",
        execute=capture_camera,
        input_schema={
            "type": "object",
            "properties": {
                "camera_index": {"type": "integer", "description": "Camera index (0 = default webcam)"},
                "filename":     {"type": "string",  "description": "Optional filename (default: timestamped)"},
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "path":    {"type": "string"},
                "size":    {"type": "string"},
                "camera":  {"type": "integer"},
            },
            "required": [],
        },
    )


def elevated_command_tool():
    """Run a command in an elevated (admin) PowerShell window."""
    def run_elevated(command: str):
        try:
            import subprocess
            # Launch PowerShell as admin — UAC prompt will appear on screen
            ps_script = f'Start-Process powershell -Verb RunAs -ArgumentList \'-NoProfile -NonInteractive -Command "{command}"\''
            subprocess.Popen(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return {"success": True, "note": "Launched elevated PowerShell — UAC prompt may appear on screen"}
        except Exception as e:
            return {"error": str(e), "success": False}

    return create_tool(
        id="run_elevated",
        description=(
            "Run a command with administrator (UAC elevated) privileges. "
            "Use when run_command fails due to permissions. "
            "A UAC confirmation dialog will appear on screen for the user to approve."
        ),
        execute=run_elevated,
        input_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "PowerShell command to run as administrator"},
            },
            "required": ["command"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "note":    {"type": "string"},
            },
            "required": [],
        },
    )
