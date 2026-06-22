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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv
from backend import JarvisBackend

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
    """Start shared backend and broadcast loop on server startup."""
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
