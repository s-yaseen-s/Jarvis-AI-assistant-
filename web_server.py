"""
J.A.R.V.I.S. Web Server
Serves the holographic web interface and bridges it to the JARVIS backend via WebSocket.
Usage:
    python jarvis.py --web          # launch web mode
    python web_server.py            # direct launch
Then open http://localhost:8000 in your browser.
"""
import asyncio
import queue
from pathlib import Path
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from backend import JarvisBackend

load_dotenv()

app = FastAPI(title="J.A.R.V.I.S.")
WEB_DIR = Path(__file__).parent / "web"

# ── Serve the web UI ────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Serve the main web UI HTML file.
    
    Returns:
        FileResponse containing the index.html file
    """
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/stats")
async def api_stats():
    """Fetch current system resource statistics.
    
    Returns:
        JSONResponse with cpu and ram percentages, or None if unavailable
    """
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        return JSONResponse({"cpu": round(cpu, 1), "ram": round(mem.percent, 1)})
    except Exception:
        return JSONResponse({"cpu": None, "ram": None})


# ── WebSocket endpoint ──────────────────────────────────────────────────────

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    """Handle WebSocket connection for real-time communication with JARVIS backend.
    
    Manages bidirectional message flow:
    - Receives user input from browser and forwards to backend
    - Receives backend responses and streams to browser
    
    Args:
        ws: WebSocket connection object
    """
    await ws.accept()
    iq = queue.Queue()   # web → backend
    oq = queue.Queue()   # backend → web

    # Start backend in its own asyncio thread
    backend = JarvisBackend(iq, oq, web_mode=True)
    backend.start()

    # Forward backend output → browser
    async def pump_output():
        """Continuously forward backend output messages to the WebSocket client."""
        while True:
            try:
                msg = oq.get_nowait()
                await ws.send_json(msg)
            except queue.Empty:
                await asyncio.sleep(0.035)
            except Exception:
                break

    pump_task = asyncio.create_task(pump_output())

    try:
        while True:
            data = await ws.receive_json()
            iq.put(data)
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        pump_task.cancel()


# ── Direct launch ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("J.A.R.V.I.S. Web Interface")
    print("Open http://localhost:4444 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=4444, log_level="warning")