"""Date and time tools for J.A.R.V.I.S.

Provides current date and time information in multiple formats.
"""

from datetime import datetime
from fury import create_tool


def get_datetime_tool():
    """Create a tool for retrieving current date and time.
    
    Returns date/time in multiple human-readable formats.
    
    Returns:
        Fury tool object for getting date/time
    """
    def get_datetime():
        """Get the current date and time in multiple formats.
        
        Returns:
            Dict with datetime, date, time, and day of week in various formats
        """
        now = datetime.now()
        return {
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "date": now.strftime("%A, %d %B %Y"),
            "time": now.strftime("%I:%M %p"),
            "day_of_week": now.strftime("%A"),
        }

    return create_tool(
        id="get_datetime",
        description="Get the current date and time",
        execute=get_datetime,
        input_schema={"type": "object", "properties": {}, "required": []},
        output_schema={
            "type": "object",
            "properties": {
                "datetime": {"type": "string"},
                "date": {"type": "string"},
                "time": {"type": "string"},
                "day_of_week": {"type": "string"},
            },
            "required": ["datetime", "date", "time", "day_of_week"],
        },
    )