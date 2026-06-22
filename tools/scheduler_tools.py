"""J.A.R.V.I.S. scheduled task management tools.

Exposes four tools for GPT-4o to create, list, remove, and immediately run
recurring tasks. The scheduler reference is injected at runtime by backend.py.

Cron quick-reference (5 fields: minute hour day month weekday):
  "0 7 * * *"     every day at 07:00
  "0 9 * * 1"     every Monday at 09:00
  "0 * * * *"     every hour on the hour
  "*/30 * * * *"  every 30 minutes
  "0 2 * * 0"     every Sunday at 02:00
  "0 8 * * 1-5"   weekdays at 08:00
"""

from datetime import datetime
from fury import create_tool

_scheduler = None   # set by backend._main() via set_scheduler()


def set_scheduler(s) -> None:
    global _scheduler
    _scheduler = s


# ── Tools ─────────────────────────────────────────────────────────────────────

def schedule_task_tool():
    def schedule_task(name: str, prompt: str, cron_expr: str) -> dict:
        """Create a persistent recurring task.

        Args:
            name: Short human-readable label (e.g. "Morning weather briefing")
            prompt: The exact command JARVIS will execute at each scheduled time
                    (e.g. "Check today's weather for Cairo and give me a summary")
            cron_expr: Standard 5-field cron expression (see module docstring)
        """
        if not _scheduler:
            return {"success": False, "error": "Scheduler not initialised yet."}
        try:
            task_id = _scheduler.add_task(name=name, prompt=prompt, cron_expr=cron_expr)
            tasks = _scheduler.list_tasks()
            t = next((x for x in tasks if x["task_id"] == task_id), {})
            nr = t.get("next_run")
            if nr:
                try:
                    nr = datetime.fromisoformat(nr).strftime("%a %d %b at %H:%M")
                except Exception:
                    pass
            return {"success": True, "task_id": task_id, "next_run": nr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    return create_tool(
        id="schedule_task",
        description=(
            "Schedule a recurring automated task that J.A.R.V.I.S. will execute "
            "without the user needing to ask. Use this when the user says anything "
            "like 'remind me every...', 'check X every...', 'send me Y at Z time'. "
            "Convert natural-language schedules to a 5-field cron expression. "
            "The prompt is the exact action JARVIS will perform on each trigger."
        ),
        execute=schedule_task,
        input_schema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Short human-readable task name (max 50 chars)",
                },
                "prompt": {
                    "type": "string",
                    "description": "Command JARVIS will execute on schedule",
                },
                "cron_expr": {
                    "type": "string",
                    "description": (
                        "5-field cron expression. Examples: "
                        "'0 7 * * *' daily at 7am | "
                        "'0 9 * * 1' Monday at 9am | "
                        "'*/30 * * * *' every 30 min | "
                        "'0 * * * *' every hour"
                    ),
                },
            },
            "required": ["name", "prompt", "cron_expr"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success":  {"type": "boolean"},
                "task_id":  {"type": "string"},
                "next_run": {"type": "string"},
                "error":    {"type": "string"},
            },
            "required": ["success"],
        },
    )


def list_tasks_tool():
    def list_tasks() -> dict:
        """Return all scheduled tasks with next-run times and recent history."""
        if not _scheduler:
            return {"tasks": [], "count": 0}
        tasks = _scheduler.list_tasks()
        for t in tasks:
            nr = t.get("next_run")
            if nr:
                try:
                    t["next_run_human"] = datetime.fromisoformat(nr).strftime(
                        "%a %d %b at %H:%M"
                    )
                except Exception:
                    t["next_run_human"] = nr
            else:
                t["next_run_human"] = "not scheduled"
        return {"tasks": tasks, "count": len(tasks)}

    return create_tool(
        id="list_tasks",
        description="List all scheduled recurring tasks with their cron schedules and next run times.",
        execute=list_tasks,
        input_schema={"type": "object", "properties": {}, "required": []},
        output_schema={
            "type": "object",
            "properties": {
                "tasks": {"type": "array"},
                "count": {"type": "integer"},
            },
            "required": ["tasks", "count"],
        },
    )


def remove_task_tool():
    def remove_task(task_id: str) -> dict:
        """Cancel and permanently delete a scheduled task by ID."""
        if not _scheduler:
            return {"success": False, "error": "Scheduler not initialised."}
        removed = _scheduler.remove_task(task_id)
        return {"success": removed, "task_id": task_id}

    return create_tool(
        id="remove_task",
        description=(
            "Cancel and permanently remove a scheduled task. "
            "Call list_tasks first to get the task_id if you don't have it."
        ),
        execute=remove_task,
        input_schema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "8-char task ID from list_tasks"},
            },
            "required": ["task_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "task_id": {"type": "string"},
            },
            "required": ["success"],
        },
    )


def run_task_now_tool():
    def run_task_now(task_id: str) -> dict:
        """Immediately execute a scheduled task without waiting for its next scheduled time."""
        if not _scheduler:
            return {"success": False, "error": "Scheduler not initialised."}
        ok = _scheduler.run_now(task_id)
        return {"success": ok, "task_id": task_id}

    return create_tool(
        id="run_task_now",
        description=(
            "Run a scheduled task immediately on demand, "
            "without waiting for its next scheduled time."
        ),
        execute=run_task_now,
        input_schema={
            "type": "object",
            "properties": {
                "task_id": {"type": "string", "description": "8-char task ID from list_tasks"},
            },
            "required": ["task_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "task_id": {"type": "string"},
            },
            "required": ["success"],
        },
    )
