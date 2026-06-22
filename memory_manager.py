"""J.A.R.V.I.S. Memory Manager

Persistent user preferences and interaction statistics backed by SQLite.
Shared across the web server and backend via a module-level global reference.

No external dependencies — uses the Python stdlib sqlite3 module only.

Tables:
  user_prefs    — key/value preference store with update timestamps
  tool_calls    — per-call records for usage analytics
  message_log   — per-message timestamps for activity heatmap

The memory_manager is safe to call from any thread because every operation
opens and closes its own SQLite connection.
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# ── Global reference ─────────────────────────────────────────────────────────
# Set once by web_server.lifespan (web mode) or backend._main() (desktop mode).
# Both share the same MemoryManager instance via this reference.

_global: Optional["MemoryManager"] = None


def set_global_memory_manager(m: "MemoryManager") -> None:
    global _global
    _global = m


def get_global_memory_manager() -> Optional["MemoryManager"]:
    return _global


# ── Preference defaults ───────────────────────────────────────────────────────

DEFAULTS: dict[str, str] = {
    "timezone":        "Africa/Cairo",
    "location":        "Cairo, Egypt",
    "tts_voice":       "onyx",
    "response_style":  "detailed",
    "language":        "en",
    "dnd_start":       "",
    "dnd_end":         "",
    "shortcuts":       "{}",
}

# Valid OpenAI TTS voices (shown in the UI dropdown)
TTS_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]


# ── Manager ───────────────────────────────────────────────────────────────────

class MemoryManager:
    """User preferences + interaction analytics for J.A.R.V.I.S.

    All public methods are thread-safe (each opens its own SQLite connection).
    Preferences persist immediately; statistics auto-prune after retention_days.
    """

    DEFAULT_DB = Path(".memory.db")

    def __init__(
        self,
        db_path: Optional[Path] = None,
        retention_days: int = 90,
    ):
        self._db = Path(db_path or os.getenv("MEMORY_DB_PATH", ".memory.db"))
        self._retention = int(os.getenv("MEMORY_RETENTION_DAYS", str(retention_days)))
        self._init_db()
        self._seed_defaults()

    # ── Schema ────────────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        with sqlite3.connect(self._db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_prefs (
                    key        TEXT PRIMARY KEY,
                    value      TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tool_calls (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_name TEXT NOT NULL,
                    called_at TEXT NOT NULL,
                    hour      INTEGER NOT NULL,
                    weekday   INTEGER NOT NULL,
                    success   INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS message_log (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    logged_at TEXT NOT NULL,
                    hour      INTEGER NOT NULL,
                    weekday   INTEGER NOT NULL
                )
            """)
            conn.commit()

    def _seed_defaults(self) -> None:
        """Insert default preferences for any key that doesn't already exist."""
        now = datetime.now().isoformat()
        with sqlite3.connect(self._db) as conn:
            for key, val in DEFAULTS.items():
                conn.execute(
                    "INSERT OR IGNORE INTO user_prefs VALUES (?,?,?)",
                    (key, val, now),
                )
            conn.commit()

    # ── Preferences ───────────────────────────────────────────────────────────

    def get_pref(self, key: str, default: Any = None) -> str:
        with sqlite3.connect(self._db) as conn:
            row = conn.execute(
                "SELECT value FROM user_prefs WHERE key=?", (key,)
            ).fetchone()
        if row:
            return row[0]
        return str(default) if default is not None else DEFAULTS.get(key, "")

    def set_pref(self, key: str, value: str) -> None:
        now = datetime.now().isoformat()
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO user_prefs VALUES (?,?,?)",
                (key, str(value), now),
            )
            conn.commit()

    def set_prefs(self, updates: dict) -> None:
        """Bulk-update multiple preferences in one transaction."""
        now = datetime.now().isoformat()
        with sqlite3.connect(self._db) as conn:
            for key, val in updates.items():
                conn.execute(
                    "INSERT OR REPLACE INTO user_prefs VALUES (?,?,?)",
                    (key, str(val), now),
                )
            conn.commit()

    def get_all_prefs(self) -> dict:
        """Return {key: {value, updated_at}} for every stored preference."""
        with sqlite3.connect(self._db) as conn:
            rows = conn.execute(
                "SELECT key, value, updated_at FROM user_prefs ORDER BY key"
            ).fetchall()
        return {r[0]: {"value": r[1], "updated_at": r[2]} for r in rows}

    # ── Interaction tracking ──────────────────────────────────────────────────

    def record_tool_call(self, tool_name: str, success: bool = True) -> None:
        now = datetime.now()
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                "INSERT INTO tool_calls (tool_name, called_at, hour, weekday, success) "
                "VALUES (?,?,?,?,?)",
                (tool_name, now.isoformat(), now.hour, now.weekday(), int(success)),
            )
            conn.commit()

    def record_message(self) -> None:
        now = datetime.now()
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                "INSERT INTO message_log (logged_at, hour, weekday) VALUES (?,?,?)",
                (now.isoformat(), now.hour, now.weekday()),
            )
            conn.commit()

    # ── Statistics ────────────────────────────────────────────────────────────

    def get_tool_stats(self, limit: int = 10) -> list:
        """Top tools by call count with success rates, limited to retention window."""
        cutoff = (datetime.now() - timedelta(days=self._retention)).isoformat()
        with sqlite3.connect(self._db) as conn:
            rows = conn.execute(
                """SELECT tool_name, COUNT(*) AS calls, SUM(success) AS ok
                   FROM tool_calls WHERE called_at > ?
                   GROUP BY tool_name ORDER BY calls DESC LIMIT ?""",
                (cutoff, limit),
            ).fetchall()
        return [
            {
                "tool":         r[0],
                "calls":        r[1],
                "success_rate": round(r[2] / r[1] * 100) if r[1] else 0,
            }
            for r in rows
        ]

    def get_hourly_activity(self) -> list:
        """Message counts for each hour 0–23 (for activity heatmap)."""
        cutoff = (datetime.now() - timedelta(days=self._retention)).isoformat()
        with sqlite3.connect(self._db) as conn:
            rows = conn.execute(
                "SELECT hour, COUNT(*) FROM message_log WHERE logged_at > ? "
                "GROUP BY hour ORDER BY hour",
                (cutoff,),
            ).fetchall()
        by_hour = {r[0]: r[1] for r in rows}
        return [{"hour": h, "count": by_hour.get(h, 0)} for h in range(24)]

    def get_summary(self) -> dict:
        """Quick totals for the settings panel header."""
        with sqlite3.connect(self._db) as conn:
            total_tools = conn.execute("SELECT COUNT(*) FROM tool_calls").fetchone()[0]
            total_msgs  = conn.execute("SELECT COUNT(*) FROM message_log").fetchone()[0]
        db_size_kb = round(self._db.stat().st_size / 1024, 1) if self._db.exists() else 0
        return {
            "total_tool_calls": total_tools,
            "total_messages":   total_msgs,
            "db_size_kb":       db_size_kb,
            "retention_days":   self._retention,
        }

    # ── Maintenance ───────────────────────────────────────────────────────────

    def prune_old_data(self) -> dict:
        """Delete records older than retention_days. Returns counts removed."""
        cutoff = (datetime.now() - timedelta(days=self._retention)).isoformat()
        with sqlite3.connect(self._db) as conn:
            tools_del = conn.execute(
                "DELETE FROM tool_calls WHERE called_at < ?", (cutoff,)
            ).rowcount
            msgs_del = conn.execute(
                "DELETE FROM message_log WHERE logged_at < ?", (cutoff,)
            ).rowcount
            conn.commit()
        return {"tool_calls_pruned": tools_del, "messages_pruned": msgs_del}

    def clear_stats(self) -> None:
        """Wipe all interaction statistics (preserves preferences)."""
        with sqlite3.connect(self._db) as conn:
            conn.execute("DELETE FROM tool_calls")
            conn.execute("DELETE FROM message_log")
            conn.commit()

    # ── System prompt injection ───────────────────────────────────────────────

    def preferences_for_prompt(self) -> str:
        """Return a formatted block for appending to the JARVIS system prompt.

        Only non-empty / non-default preferences are included to keep the
        prompt lean. Called once at agent initialization; TTS voice is the
        only preference re-read on each response (via get_pref()).
        """
        tz    = self.get_pref("timezone")
        loc   = self.get_pref("location")
        style = self.get_pref("response_style")
        lang  = self.get_pref("language")
        dnd_s = self.get_pref("dnd_start")
        dnd_e = self.get_pref("dnd_end")
        sc    = self.get_pref("shortcuts")

        style_hint = {
            "concise":  "be brief and direct — one or two sentences maximum unless detail is explicitly requested",
            "detailed": "give thorough explanations with context",
            "creative": "be expressive and elaborate — show personality, add colour",
        }.get(style, "")

        lines = [
            "",
            "USER PREFERENCES (auto-loaded from .memory.db):",
            f"• Timezone: {tz}  — use for all time calculations and scheduling",
            f"• Location: {loc}  — use for weather, news, and local information",
            f"• Response style: {style}" + (f" — {style_hint}" if style_hint else ""),
            f"• Language: {lang}",
        ]
        if dnd_s and dnd_e:
            lines.append(
                f"• Do Not Disturb: {dnd_s}–{dnd_e}  "
                f"— suppress scheduled task alerts during this window"
            )
        if sc and sc not in ("{}", ""):
            lines.append(f"• Command shortcuts: {sc}  — expand these when the user types them")
        lines.append(
            "Use get_preference / set_preference tools to read or update any preference. "
            "TTS voice changes take effect immediately; all other preferences take effect "
            "on the next server restart."
        )
        return "\n".join(lines)
