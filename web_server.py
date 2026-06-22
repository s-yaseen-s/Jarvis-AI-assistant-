"""
J.A.R.V.I.S. Web Server
Serves the holographic web interface and bridges it to the JARVIS backend via WebSocket.

Multi-device sync: one shared backend broadcasts to all connected clients simultaneously.
All devices share the same conversation context, memory, and agent state.

Usage:
    python jarvis.py --web          # launch web mode
    python web_server.py            # direct launch
Then open http://localhost:4444 from any device on the network.

Auth (optional):
    Set JARVIS_TOKEN=your-secret in .env, then access with:
    http://host:4444?token=your-secret
    Token is saved in browser localStorage after first visit.
"""
import asyncio
import os
import queue
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Set

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
from backend import JarvisBackend
from task_scheduler import get_global_scheduler
from memory_manager import MemoryManager, set_global_memory_manager, get_global_memory_manager

load_dotenv()

WEB_DIR = Path(__file__).parent / "web"

# ── Singleton backend ─────────────────────────────────────────────────────────
# One backend instance shared across ALL WebSocket connections.
# All devices see the same conversation, memory, and agent state.
_iq: queue.Queue = queue.Queue()   # any client → backend
_oq: queue.Queue = queue.Queue()   # backend → all clients
_backend = JarvisBackend(_iq, _oq, web_mode=True)
_clients: Set[WebSocket] = set()


async def _broadcast_loop() -> None:
    """Fan out backend output to every connected WebSocket client."""
    while True:
        try:
            msg = _oq.get_nowait()
            dead: Set[WebSocket] = set()
            for client in list(_clients):
                try:
                    await client.send_json(msg)
                except Exception:
                    dead.add(client)
            _clients -= dead
        except queue.Empty:
            await asyncio.sleep(0.035)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start memory manager, shared backend, and broadcast loop on server startup."""
    # Init memory manager first so backend can read preferences during agent init
    mm = MemoryManager()
    set_global_memory_manager(mm)

    _backend.start()
    task = asyncio.create_task(_broadcast_loop())
    yield
    task.cancel()


app = FastAPI(title="J.A.R.V.I.S.", lifespan=lifespan)


# ── Auth helper ───────────────────────────────────────────────────────────────

def _auth_ok(token: str | None) -> bool:
    """Return True if the provided token matches JARVIS_TOKEN env var.
    If JARVIS_TOKEN is not set, all connections are allowed (LAN-only mode)."""
    required = os.getenv("JARVIS_TOKEN", "").strip()
    if not required:
        return True
    return token == required


# ── HTTP routes ───────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve the main web UI."""
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/stats")
async def api_stats():
    """Current system resource statistics."""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        return JSONResponse({"cpu": round(cpu, 1), "ram": round(mem.percent, 1)})
    except Exception:
        return JSONResponse({"cpu": None, "ram": None})


@app.get("/api/auth")
async def api_auth():
    """Tell clients whether a token is required to connect."""
    return JSONResponse({"required": bool(os.getenv("JARVIS_TOKEN", "").strip())})


# ── Task scheduler REST API ───────────────────────────────────────────────────

@app.get("/api/tasks")
async def api_tasks_list():
    """Return all scheduled tasks with next-run times and recent history."""
    s = get_global_scheduler()
    return JSONResponse({"tasks": s.list_tasks() if s else []})


@app.post("/api/tasks")
async def api_tasks_create(request: Request):
    """Create a new scheduled task. Body: {name, prompt, cron_expr}."""
    s = get_global_scheduler()
    if not s:
        return JSONResponse({"ok": False, "error": "Scheduler not ready"}, status_code=503)
    try:
        body = await request.json()
        task_id = s.add_task(body["name"], body["prompt"], body["cron_expr"])
        return JSONResponse({"ok": True, "task_id": task_id})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


@app.delete("/api/tasks/{task_id}")
async def api_tasks_delete(task_id: str):
    """Cancel and remove a scheduled task."""
    s = get_global_scheduler()
    if not s:
        return JSONResponse({"ok": False, "error": "Scheduler not ready"}, status_code=503)
    removed = s.remove_task(task_id)
    return JSONResponse({"ok": removed})


@app.post("/api/tasks/{task_id}/run")
async def api_tasks_run_now(task_id: str):
    """Immediately fire a scheduled task without waiting for its next cron time."""
    s = get_global_scheduler()
    if not s:
        return JSONResponse({"ok": False, "error": "Scheduler not ready"}, status_code=503)
    ok = s.run_now(task_id)
    return JSONResponse({"ok": ok})


# ── Preferences REST API ──────────────────────────────────────────────────────

@app.get("/api/preferences")
async def api_prefs_get():
    """Return all user preferences as {key: {value, updated_at}}."""
    mm = get_global_memory_manager()
    if not mm:
        return JSONResponse({"prefs": {}})
    return JSONResponse({"prefs": mm.get_all_prefs()})


@app.post("/api/preferences")
async def api_prefs_set(request: Request):
    """Bulk-update preferences. Body: {key: value, ...}."""
    mm = get_global_memory_manager()
    if not mm:
        return JSONResponse({"ok": False, "error": "Memory manager not ready"}, status_code=503)
    try:
        updates = await request.json()
        mm.set_prefs(updates)
        return JSONResponse({"ok": True, "updated": list(updates.keys())})
    except Exception as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)


# ── Statistics REST API ───────────────────────────────────────────────────────

@app.get("/api/stats")
async def api_stats_full():
    """Tool usage stats, hourly activity, and storage summary."""
    mm = get_global_memory_manager()
    if not mm:
        return JSONResponse({"tools": [], "hourly": [], "summary": {}})
    return JSONResponse({
        "tools":   mm.get_tool_stats(),
        "hourly":  mm.get_hourly_activity(),
        "summary": mm.get_summary(),
    })


@app.delete("/api/stats")
async def api_stats_clear():
    """Clear all interaction statistics (preserves preferences)."""
    mm = get_global_memory_manager()
    if not mm:
        return JSONResponse({"ok": False, "error": "Memory manager not ready"}, status_code=503)
    mm.clear_stats()
    return JSONResponse({"ok": True})


@app.get("/api/clients")
async def api_clients():
    """Number of currently connected devices."""
    return JSONResponse({"connected": len(_clients)})


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket, token: str = Query(default=None)):
    """Accept a client, check auth, then relay messages to the shared backend.
    Close code 4001 = unauthorized (client should not retry automatically)."""
    if not _auth_ok(token):
        await ws.close(code=4001, reason="Unauthorized")
        return

    await ws.accept()
    _clients.add(ws)

    try:
        while True:
            data = await ws.receive_json()
            _iq.put(data)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        _clients.discard(ws)


# ── Direct launch ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("J.A.R.V.I.S. Web Interface → http://localhost:4444")
    print("Access from any device on the network using your machine's IP.")
    uvicorn.run(app, host="0.0.0.0", port=4444, log_level="warning")
