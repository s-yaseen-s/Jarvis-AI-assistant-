from datetime import datetime
from fury import create_tool


def get_datetime_tool():
    def get_datetime():
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
