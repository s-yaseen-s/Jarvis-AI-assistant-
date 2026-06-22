import json
from datetime import datetime
from pathlib import Path
from fury import create_tool

NOTES_FILE = Path(".fury/notes.json")


def _load() -> list:
    if NOTES_FILE.exists():
        return json.loads(NOTES_FILE.read_text(encoding="utf-8"))
    return []


def _save(notes: list) -> None:
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)
    NOTES_FILE.write_text(json.dumps(notes, indent=2, ensure_ascii=False), encoding="utf-8")


def write_note_tool():
    def write_note(content: str, title: str = ""):
        notes = _load()
        note = {
            "id": len(notes) + 1,
            "title": title or f"Note {len(notes) + 1}",
            "content": content,
            "created_at": datetime.now().isoformat(),
        }
        notes.append(note)
        _save(notes)
        return {"success": True, "note_id": note["id"], "title": note["title"]}

    return create_tool(
        id="write_note",
        description="Save a note, reminder, or piece of information for later retrieval",
        execute=write_note,
        input_schema={
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "The note content to save"},
                "title": {"type": "string", "description": "Optional short title for the note"},
            },
            "required": ["content"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "note_id": {"type": "integer"},
                "title": {"type": "string"},
            },
            "required": ["success"],
        },
    )


def read_notes_tool():
    def read_notes(limit: int = 10):
        notes = _load()
        return {"notes": notes[-limit:], "total": len(notes)}

    return create_tool(
        id="read_notes",
        description="Read saved notes and reminders",
        execute=read_notes,
        input_schema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "How many recent notes to return (default 10)"},
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "notes": {"type": "array"},
                "total": {"type": "integer"},
            },
            "required": ["notes", "total"],
        },
    )
