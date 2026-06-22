"""J.A.R.V.I.S. user preference management tools.

Three tools let GPT-4o read and update persistent preferences conversationally.
The MemoryManager reference is injected at runtime by backend._main().

Examples:
    "Set my timezone to Asia/Dubai"
        → set_preference(key="timezone", value="Asia/Dubai")

    "What voice am I using?"
        → get_preference(key="tts_voice")

    "Show me all my settings"
        → list_preferences()
"""

from fury import create_tool

_mm = None   # set by backend._main() via set_memory_manager()


def set_memory_manager(m) -> None:
    global _mm
    _mm = m


# ── Tools ─────────────────────────────────────────────────────────────────────

def get_preference_tool():
    def get_preference(key: str) -> dict:
        """Read a single user preference by key."""
        if not _mm:
            return {"success": False, "error": "Memory manager not initialised."}
        value = _mm.get_pref(key)
        return {"success": True, "key": key, "value": value}

    return create_tool(
        id="get_preference",
        description=(
            "Read a stored user preference. "
            "Keys: timezone, location, tts_voice, response_style, language, "
            "dnd_start, dnd_end, shortcuts."
        ),
        execute=get_preference,
        input_schema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Preference key to read"},
            },
            "required": ["key"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "key":     {"type": "string"},
                "value":   {"type": "string"},
                "error":   {"type": "string"},
            },
            "required": ["success"],
        },
    )


def set_preference_tool():
    def set_preference(key: str, value: str) -> dict:
        """Update a user preference.

        Args:
            key: Preference name. Valid keys and accepted values:
                 • timezone       — IANA timezone (e.g. "Africa/Cairo", "Europe/London")
                 • location       — City/country string (e.g. "Cairo, Egypt")
                 • tts_voice      — One of: alloy, echo, fable, onyx, nova, shimmer
                                    (onyx = deep male, nova = warm female)
                                    Takes effect IMMEDIATELY on next response.
                 • response_style — "concise" | "detailed" | "creative"
                                    Takes effect on next server restart.
                 • language       — ISO language code (e.g. "en", "ar", "fr")
                 • dnd_start      — Do Not Disturb start time "HH:MM" or "" to disable
                 • dnd_end        — Do Not Disturb end time "HH:MM" or "" to disable
                 • shortcuts      — JSON object mapping short codes to full commands
                                    (e.g. '{"W": "What is the weather?"}')
            value: New value for the preference.
        """
        if not _mm:
            return {"success": False, "error": "Memory manager not initialised."}
        _mm.set_pref(key, value)
        return {
            "success": True,
            "key": key,
            "value": value,
            "note": "TTS voice changes take effect immediately. All other preferences take effect on next server restart.",
        }

    return create_tool(
        id="set_preference",
        description=(
            "Update a persistent user preference. "
            "TTS voice (onyx/nova/echo/etc) changes take effect immediately. "
            "Timezone, location, response_style, and language take effect on "
            "the next server restart."
        ),
        execute=set_preference,
        input_schema={
            "type": "object",
            "properties": {
                "key":   {"type": "string", "description": "Preference key to update"},
                "value": {"type": "string", "description": "New value"},
            },
            "required": ["key", "value"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "key":     {"type": "string"},
                "value":   {"type": "string"},
                "note":    {"type": "string"},
                "error":   {"type": "string"},
            },
            "required": ["success"],
        },
    )


def list_preferences_tool():
    def list_preferences() -> dict:
        """Return all stored user preferences as a flat key→value dict."""
        if not _mm:
            return {"success": False, "prefs": {}, "error": "Memory manager not initialised."}
        raw = _mm.get_all_prefs()
        flat = {k: v["value"] for k, v in raw.items()}
        return {"success": True, "prefs": flat}

    return create_tool(
        id="list_preferences",
        description="List all current user preferences (timezone, location, voice, style, etc.).",
        execute=list_preferences,
        input_schema={"type": "object", "properties": {}, "required": []},
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "prefs":   {"type": "object"},
                "error":   {"type": "string"},
            },
            "required": ["success", "prefs"],
        },
    )
