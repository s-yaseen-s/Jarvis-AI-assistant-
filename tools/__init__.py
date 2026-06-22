from .datetime_tools   import get_datetime_tool
from .web_tools        import web_search_tool, get_weather_tool, fetch_page_tool
from .system_tools     import system_info_tool, open_app_tool
from .notes_tools      import write_note_tool, read_notes_tool
from .timer_tools      import timer_tool, set_alert_queue
from .volume_tools     import volume_tool
from .screenshot_tools import screenshot_tool as take_screenshot_tool
from .news_tools       import news_tool
from .browser_tools    import open_url_tool, youtube_search_tool, google_search_browser_tool
from .filesystem_tools import (list_directory_tool, read_file_tool,
                                write_file_tool, delete_file_tool, move_file_tool)
from .shell_tools      import run_command_tool, list_processes_tool, kill_process_tool
from .clipboard_tools  import get_clipboard_tool, set_clipboard_tool
from .keyboard_tools   import press_hotkey_tool, type_text_tool, mouse_click_tool
from .learning_tools   import (save_skill_tool, list_skills_tool,
                                self_reflect_tool, get_reflections_tool)
from .private_mode_tool import private_mode_tool, set_output_queue as set_private_mode_queue
from .camera_tools      import capture_camera_tool, elevated_command_tool
from .screen_tools      import read_screen_tool
from .calendar_tools    import (list_events_tool, today_events_tool,
                                create_event_tool, delete_event_tool, update_event_tool)
from .gmail_tools       import (list_emails_tool, read_email_tool,
                                search_emails_tool, send_email_tool)
# self_modify_tool intentionally disabled — JARVIS cannot edit his own source files


def get_all_tools():
    return [
        # Time & info
        get_datetime_tool(),
        # Web
        web_search_tool(),
        fetch_page_tool(),
        get_weather_tool(),
        news_tool(),
        # Browser navigation
        open_url_tool(),
        youtube_search_tool(),
        google_search_browser_tool(),
        # System
        system_info_tool(),
        open_app_tool(),
        run_command_tool(),
        list_processes_tool(),
        kill_process_tool(),
        # Files
        list_directory_tool(),
        read_file_tool(),
        write_file_tool(),
        delete_file_tool(),
        move_file_tool(),
        # Interaction
        get_clipboard_tool(),
        set_clipboard_tool(),
        press_hotkey_tool(),
        type_text_tool(),
        mouse_click_tool(),
        # Output
        take_screenshot_tool(),
        volume_tool(),
        # Notes & reminders
        write_note_tool(),
        read_notes_tool(),
        timer_tool(),
        # Learning
        save_skill_tool(),
        list_skills_tool(),
        self_reflect_tool(),
        get_reflections_tool(),
        # Privacy
        private_mode_tool(),
        # Camera & screen
        capture_camera_tool(),
        read_screen_tool(),
        # Elevated commands
        elevated_command_tool(),
        # Google Calendar
        list_events_tool(),
        today_events_tool(),
        create_event_tool(),
        delete_event_tool(),
        update_event_tool(),
        # Gmail
        list_emails_tool(),
        read_email_tool(),
        search_emails_tool(),
        send_email_tool(),
        # Self-modification disabled
    ]
