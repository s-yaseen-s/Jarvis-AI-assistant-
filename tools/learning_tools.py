"""Self-learning and skill persistence tools for J.A.R.V.I.S.

Allows J.A.R.V.I.S. to save reusable skills (multi-step procedures) and
record self-reflections/lessons learned for future sessions.
"""

import json
from datetime import datetime
from pathlib import Path
from fury import create_tool

SKILLS_FILE      = Path(".fury/skills.json")
REFLECTIONS_FILE = Path(".fury/self_reflections.json")


def _load(path: Path) -> list:
    """Load data from a JSON file.
    
    Args:
        path: Path to JSON file
        
    Returns:
        List of objects from JSON, or empty list if file doesn't exist
    """
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def _save(path: Path, data) -> None:
    """Save data to a JSON file.
    
    Creates parent directories as needed.
    
    Args:
        path: Path to JSON file to write
        data: Object to serialize as JSON
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ── Skills ──────────────────────────────────────────────────────────────────

def save_skill_tool():
    """Create a tool for saving reusable named skills.
    
    A skill is a sequence of steps to accomplish a recurring task.
    Can be updated by saving with the same name.
    
    Returns:
        Fury tool object for saving skills
    """
    def save_skill(name: str, description: str, steps: list):
        """Save a named skill — a sequence of steps to accomplish a task.
        
        Call this after successfully completing a complex task so it can be
        repeated more efficiently in the future. Saves to persistent storage.
        
        Args:
            name: Short unique skill name (e.g., 'open_youtube_song')
            description: What this skill does
            steps: Ordered list of step descriptions to follow
            
        Returns:
            Dict with success status, skill name, and step count
        """
        skills = _load(SKILLS_FILE)
        existing = next((i for i, s in enumerate(skills) if s["name"] == name), None)
        skill = {
            "name":        name,
            "description": description,
            "steps":       steps,
            "updated_at":  datetime.now().isoformat(),
        }
        if existing is not None:
            skills[existing] = skill
        else:
            skills.append(skill)
        _save(SKILLS_FILE, skills)
        return {"success": True, "name": name, "steps_count": len(steps)}

    return create_tool(
        id="save_skill",
        description=(
            "Save a named skill — a sequence of steps to accomplish a recurring task. "
            "Call this after successfully completing a complex task so you can repeat it "
            "more efficiently in the future."
        ),
        execute=save_skill,
        input_schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Short unique skill name, e.g. 'open_youtube_song'",
                },
                "description": {
                    "type": "string",
                    "description": "What this skill does",
                },
                "steps": {
                    "type": "array",
                    "description": "Ordered list of step descriptions",
                    "items": {"type": "string"},
                },
            },
            "required": ["name", "description", "steps"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success":     {"type": "boolean"},
                "name":        {"type": "string"},
                "steps_count": {"type": "integer"},
            },
            "required": [],
        },
    )


def list_skills_tool():
    """Create a tool for listing all saved skills.
    
    Returns:
        Fury tool object for listing skills
    """
    def list_skills():
        """List all saved skills and their descriptions.
        
        Returns:
            Dict with skills list and total count
        """
        skills = _load(SKILLS_FILE)
        return {"skills": skills, "count": len(skills)}

    return create_tool(
        id="list_skills",
        description="List all saved skills and their descriptions",
        execute=list_skills,
        input_schema={"type": "object", "properties": {}, "required": []},
        output_schema={
            "type": "object",
            "properties": {
                "skills": {"type": "array"},
                "count":  {"type": "integer"},
            },
            "required": ["skills"],
        },
    )


# ── Self-reflection ─────────────────────────────────────────────────────────

def self_reflect_tool():
    """Create a tool for recording self-reflections and lessons learned.
    
    Stores insights and lessons that improve future behavior.
    Useful for recording user preferences, working tool patterns, etc.
    
    Returns:
        Fury tool object for self-reflection
    """
    def self_reflect(insight: str, category: str = "general"):
        """Record a lesson or insight to improve future performance.
        
        Use this when discovering something about the user's environment,
        preferences, or a better way to accomplish a task. These reflections
        are stored and can inform future decisions.
        
        Args:
            insight: The lesson or insight to record
            category: Category type (general | browser | system | user_preference | tool_usage)
            
        Returns:
            Dict with success status and total reflection count
        """
        entries = _load(REFLECTIONS_FILE)
        entries.append({
            "insight":    insight,
            "category":   category,
            "recorded_at": datetime.now().isoformat(),
        })
        _save(REFLECTIONS_FILE, entries)
        return {"success": True, "total_reflections": len(entries)}

    return create_tool(
        id="self_reflect",
        description=(
            "Record a lesson or insight to improve future performance. "
            "Use this when you discover something about the user's environment, "
            "preferences, or a better way to do a task. "
            "Examples: 'User prefers Brave browser', "
            "'YouTube search works via youtube_search tool not open_application', "
            "'open_application with full path works better than short name'."
        ),
        execute=self_reflect,
        input_schema={
            "type": "object",
            "properties": {
                "insight": {
                    "type": "string",
                    "description": "The lesson or insight to record",
                },
                "category": {
                    "type": "string",
                    "description": "Category: general | browser | system | user_preference | tool_usage",
                },
            },
            "required": ["insight"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success":           {"type": "boolean"},
                "total_reflections": {"type": "integer"},
            },
            "required": [],
        },
    )


def get_reflections_tool():
    """Create a tool for retrieving stored reflections.
    
    Returns:
        Fury tool object for getting reflections
    """
    def get_reflections(category: str = ""):
        """Retrieve stored self-reflections and lessons learned.
        
        Args:
            category: Optional filter by category (empty string = all)
            
        Returns:
            Dict with reflections list and count
        """
        entries = _load(REFLECTIONS_FILE)
        if category:
            entries = [e for e in entries if e.get("category") == category]
        return {"reflections": entries, "count": len(entries)}

    return create_tool(
        id="get_reflections",
        description="Retrieve stored self-reflections and lessons learned",
        execute=get_reflections,
        input_schema={
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category (empty = all)",
                },
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "reflections": {"type": "array"},
                "count":       {"type": "integer"},
            },
            "required": ["reflections"],
        },
    )