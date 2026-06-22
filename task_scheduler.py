"""J.A.R.V.I.S. Persistent Task Scheduler

APScheduler-backed scheduled tasks that survive restarts and broadcast
execution results to all connected WebSocket clients.

When a task fires, its prompt is injected into the backend input queue
as a regular text message. JARVIS processes it with its full tool suite
and the response is broadcast to all connected devices automatically.

Storage layout in .tasks.db (SQLite):
  apscheduler_jobs — managed by APScheduler (cron triggers, next-run times)
  task_meta        — human-readable names, prompts, enabled flag
  task_runs        — execution history (last 20 runs per task)
"""

import queue
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger

# ── Global reference (set by backend after init, read by web_server) ─────────

_global: Optional["JarvisScheduler"] = None


def set_global_scheduler(s: "JarvisScheduler") -> None:
    global _global
    _global = s


def get_global_scheduler() -> Optional["JarvisScheduler"]:
    return _global


# ── Scheduler ────────────────────────────────────────────────────────────────

class JarvisScheduler:
    """Persistent async task scheduler for J.A.R.V.I.S.

    Must be started inside a running asyncio event loop (call start() from
    an async coroutine). Uses APScheduler's AsyncIOScheduler so jobs fire
    in the same event loop as the backend agent — no cross-thread issues.

    Thread safety: list_tasks() and run_now() are safe to call from any
    thread. add_task() / remove_task() call APScheduler methods that use
    call_soon_threadsafe internally, so the web server can call them too.
    """

    DEFAULT_DB = Path(".tasks.db")

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        db_path: Optional[Path] = None,
    ):
        self._iq = input_queue
        self._oq = output_queue
        self._db = Path(db_path or self.DEFAULT_DB)

        db_url = f"sqlite:///{self._db}"
        self._aps = AsyncIOScheduler(
            jobstores={"default": SQLAlchemyJobStore(url=db_url)},
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 120,
            },
        )
        self._init_db()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _init_db(self) -> None:
        with sqlite3.connect(self._db) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_meta (
                    task_id    TEXT PRIMARY KEY,
                    name       TEXT NOT NULL,
                    prompt     TEXT NOT NULL,
                    cron_expr  TEXT NOT NULL,
                    enabled    INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS task_runs (
                    id       INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id  TEXT NOT NULL,
                    run_at   TEXT NOT NULL,
                    status   TEXT NOT NULL,
                    error    TEXT
                )
            """)
            conn.commit()

    def start(self) -> None:
        """Start the scheduler. Must be called from within a running asyncio event loop."""
        self._aps.start()
        self._restore_jobs()

    def _restore_jobs(self) -> None:
        """Re-register task_meta rows whose APScheduler job disappeared after restart."""
        with sqlite3.connect(self._db) as conn:
            rows = conn.execute(
                "SELECT task_id, prompt, cron_expr FROM task_meta WHERE enabled=1"
            ).fetchall()
        for task_id, prompt, cron_expr in rows:
            if not self._aps.get_job(task_id):
                try:
                    self._register(task_id, prompt, cron_expr)
                except Exception as e:
                    print(f"[Scheduler] Could not restore job {task_id}: {e}")

    def _register(self, task_id: str, prompt: str, cron_expr: str) -> None:
        """Add or replace a job in APScheduler from a 5-field cron string."""
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            raise ValueError(
                f"cron_expr must have exactly 5 fields (got {len(parts)}): {cron_expr!r}\n"
                "Examples: '0 7 * * *' = daily 7am  |  '0 9 * * 1' = Monday 9am  |  "
                "'*/30 * * * *' = every 30 min  |  '0 * * * *' = every hour"
            )
        minute, hour, day, month, dow = parts
        self._aps.add_job(
            func=self._fire,
            trigger=CronTrigger(
                minute=minute, hour=hour, day=day, month=month, day_of_week=dow
            ),
            id=task_id,
            args=[task_id, prompt],
            replace_existing=True,
        )

    # ── Public CRUD ───────────────────────────────────────────────────────────

    def add_task(self, name: str, prompt: str, cron_expr: str) -> str:
        """Create a persistent scheduled task. Returns the new task_id."""
        task_id = uuid.uuid4().hex[:8]
        self._register(task_id, prompt, cron_expr)
        with sqlite3.connect(self._db) as conn:
            conn.execute(
                "INSERT INTO task_meta VALUES (?,?,?,?,1,?)",
                (task_id, name, prompt, cron_expr, datetime.now().isoformat()),
            )
            conn.commit()
        self._push_update()
        return task_id

    def remove_task(self, task_id: str) -> bool:
        """Cancel and delete a task. Returns True if it existed."""
        job = self._aps.get_job(task_id)
        if job:
            self._aps.remove_job(task_id)
        with sqlite3.connect(self._db) as conn:
            n = conn.execute(
                "DELETE FROM task_meta WHERE task_id=?", (task_id,)
            ).rowcount
            conn.commit()
        if n:
            self._push_update()
        return bool(n)

    def list_tasks(self) -> list:
        """Return all tasks with next-run times and recent execution history."""
        with sqlite3.connect(self._db) as conn:
            rows = conn.execute(
                "SELECT task_id, name, prompt, cron_expr, enabled, created_at "
                "FROM task_meta ORDER BY created_at"
            ).fetchall()

        tasks = []
        for task_id, name, prompt, cron_expr, enabled, created_at in rows:
            job = self._aps.get_job(task_id)
            next_run = (
                job.next_run_time.isoformat()
                if job and job.next_run_time
                else None
            )
            with sqlite3.connect(self._db) as conn:
                runs = conn.execute(
                    "SELECT run_at, status FROM task_runs "
                    "WHERE task_id=? ORDER BY id DESC LIMIT 5",
                    (task_id,),
                ).fetchall()
            tasks.append(
                {
                    "task_id":     task_id,
                    "name":        name,
                    "prompt":      prompt,
                    "cron_expr":   cron_expr,
                    "enabled":     bool(enabled),
                    "created_at":  created_at,
                    "next_run":    next_run,
                    "recent_runs": [{"run_at": r[0], "status": r[1]} for r in runs],
                }
            )
        return tasks

    def run_now(self, task_id: str) -> bool:
        """Immediately fire a task by injecting its prompt into the backend queue."""
        with sqlite3.connect(self._db) as conn:
            row = conn.execute(
                "SELECT prompt FROM task_meta WHERE task_id=?", (task_id,)
            ).fetchone()
        if not row:
            return False
        self._fire(task_id, row[0])
        return True

    # ── Internal ──────────────────────────────────────────────────────────────

    def _fire(self, task_id: str, prompt: str) -> None:
        """Triggered by APScheduler or run_now. Injects prompt into the backend."""
        run_at = datetime.now().isoformat()

        # Tell all clients which scheduled task just fired
        self._oq.put({"type": "task_fired", "task_id": task_id, "time": run_at})

        # Inject as a user text message — JARVIS executes it with all its tools
        self._iq.put({"type": "text", "content": f"[SCHEDULED] {prompt}"})

        # Persist execution record
        try:
            with sqlite3.connect(self._db) as conn:
                conn.execute(
                    "INSERT INTO task_runs (task_id, run_at, status) VALUES (?,?,'ok')",
                    (task_id, run_at),
                )
                # Keep only last 20 runs per task to prevent unbounded growth
                conn.execute(
                    """DELETE FROM task_runs WHERE task_id=? AND id NOT IN (
                           SELECT id FROM task_runs WHERE task_id=?
                           ORDER BY id DESC LIMIT 20
                       )""",
                    (task_id, task_id),
                )
                conn.commit()
        except Exception as e:
            print(f"[Scheduler] History write failed for {task_id}: {e}")

    def _push_update(self) -> None:
        """Broadcast a fresh task list to all connected WebSocket clients."""
        try:
            self._oq.put({"type": "tasks_update", "tasks": self.list_tasks()})
        except Exception:
            pass
