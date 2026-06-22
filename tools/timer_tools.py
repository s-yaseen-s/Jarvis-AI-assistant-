"""Timer and alert tools for J.A.R.V.I.S.

Provides countdown timer functionality with audio/visual alerts.
Timers run asynchronously in background threads.
"""

import queue
import threading
from fury import create_tool

_alert_queue: queue.Queue | None = None


def set_alert_queue(q: queue.Queue):
    """Register the alert queue for timer notifications.
    
    This queue is used to send alert messages when timers expire.
    
    Args:
        q: Queue object for receiving timer alerts
    """
    global _alert_queue
    _alert_queue = q


def timer_tool():
    """Create a tool for setting countdown timers.
    
    Timers run in background threads and send alerts when time expires.
    
    Returns:
        Fury tool object for setting timers
    """
    def set_timer(seconds: int, label: str = "Timer"):
        """Set a countdown timer with optional label.
        
        Timer runs in background and sends an alert when done.
        
        Args:
            seconds: Duration in seconds
            label: Optional name/label for the timer (e.g., 'pasta', 'reminder')
            
        Returns:
            Dict with success status, timer label, and human-readable duration
        """
        def _fire():
            """Fire the timer alert when countdown reaches zero."""
            if _alert_queue:
                _alert_queue.put({"type": "alert",
                                  "message": f"⏰ {label} — time's up!"})
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