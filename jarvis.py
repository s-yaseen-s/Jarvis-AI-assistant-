"""
J.A.R.V.I.S. — Just A Rather Very Intelligent System
Entry point.

  python jarvis.py          # tkinter holographic desktop GUI
  python jarvis.py --web    # browser-based holographic interface (http://localhost:4444)
"""

import sys
from dotenv import load_dotenv

load_dotenv()


def run_desktop():
    import queue
    import tkinter as tk
    from backend import JarvisBackend
    from gui import JarvisUI

    iq = queue.Queue()
    oq = queue.Queue()
    JarvisBackend(iq, oq).start()
    root = tk.Tk()
    JarvisUI(root, iq, oq)
    root.mainloop()


def run_web(port: int = 4444):
    import uvicorn
    print(f"J.A.R.V.I.S. Web Interface → http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    # reload=True: server auto-restarts when any source file changes
    # This lets JARVIS modify his own code and apply it instantly
    uvicorn.run("web_server:app", host="0.0.0.0", port=port,
                log_level="warning", reload=True,
                reload_dirs=["D:/Desktop/Github_Jarvis"])


if __name__ == "__main__":
    if "--web" in sys.argv:
        idx = sys.argv.index("--web")
        port = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) and sys.argv[idx + 1].isdigit() else 4444
        run_web(port)
    else:
        run_desktop()
