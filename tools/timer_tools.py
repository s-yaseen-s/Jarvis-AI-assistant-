import queue
import threading
from fury import create_tool

_alert_queue: queue.Queue | None = None


def set_alert_queue(q: queue.Queue):
    global _alert_queue
    _alert_queue = q


def timer_tool():
    def set_timer(seconds: int, label: str = "Timer"):
        def _fire():
            if _alert_queue:
                _alert_queue.put({"type": "alert",
                                  "message": f"⏰  {label} — time's up!"})

        t = threading.Timer(float(seconds), _fire)
        t.daemon = True
        t.start()
        mins, secs = divmod(seconds, 60)
        human = f"{mins}m {secs}s" if mins else f"{secs}s"
        return {"success": True, "label": label, "duration": human}

    return create_tool(
        id="set_timer",
        description="Set a countdown timer that alerts when done",
        execute=set_timer,
        input_schema={
            "type": "object",
            "properties": {
                "seconds": {"type": "integer", "description": "Duration in seconds"},
                "label":   {"type": "string",  "description": "Timer name (e.g. 'pasta')"},
            },
            "required": ["seconds"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success":  {"type": "boolean"},
                "label":    {"type": "string"},
                "duration": {"type": "string"},
            },
            "required": ["success"],
        },
    )
