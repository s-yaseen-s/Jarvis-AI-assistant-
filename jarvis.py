"""J.A.R.V.I.S. — Just A Rather Very Intelligent System

Production-ready voice-controlled AI assistant with dual interface support.

Entry Points:
    Desktop Mode:  python jarvis.py
                   Launches tkinter holographic GUI with voice control
    
    Web Mode:      python jarvis.py --web [port]
                   Browser-based interface at http://localhost:4444 (default)
                   Auto-reloads on code changes for rapid development
    
    Custom Port:   python jarvis.py --web 8000
                   Runs web server on specified port

Environment:
    Requires .env file with API keys (OPENAI_API_KEY, FURY_API_KEY, etc.)
    Uses credentials.json for Google OAuth2 authentication
    Auto-loads environment variables on startup

Architecture:
    - Backend: Async AI agent (fury-sdk) running in daemon thread
    - Desktop UI: tkinter with real-time visualization
    - Web UI: FastAPI with browser control panel
    - Inter-process Communication: Queue-based message passing
"""

import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def run_desktop():
    """Launch J.A.R.V.I.S. with desktop (tkinter) interface.
    
    Creates separate threads for:
    - Backend: Async AI agent processing commands
    - GUI: tkinter event loop for user interaction
    
    Uses queue-based IPC for communication between threads.
    Blocks on root.mainloop() until user closes window.
    
    Raises:
        ImportError: If tkinter is not available
        Exception: If backend fails to initialize
    """
    import queue
    import tkinter as tk
    from backend import JarvisBackend
    from gui import JarvisUI

    # Create inter-process communication queues
    input_queue = queue.Queue()      # User input → Backend
    output_queue = queue.Queue()     # Backend output → GUI

    # Start backend in daemon thread
    JarvisBackend(input_queue, output_queue).start()

    # Create and run tkinter GUI
    root = tk.Tk()
    JarvisUI(root, input_queue, output_queue)
    root.mainloop()


def run_web(port: int = 4444):
    """Launch J.A.R.V.I.S. with web (browser) interface.
    
    Starts FastAPI server on specified port with auto-reload enabled.
    Auto-reload allows J.A.R.V.I.S. to modify its own code and apply
    changes instantly without manual restart.
    
    Features:
    - Hot-reload on file changes (live coding)
    - Browser-based control panel
    - Remote access capability
    - JSON API for programmatic control
    
    Args:
        port: Port number for web server (default: 4444)
        
    Raises:
        Exception: If port is already in use or binding fails
    """
    import uvicorn

    print(f"J.A.R.V.I.S. Web Interface → http://localhost:{port}")
    print("Press Ctrl+C to stop.")
    print("Auto-reload enabled: changes to source files apply instantly")

    # Start uvicorn server with hot-reload enabled
    # reload_dirs watches the project directory for changes
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=port,
        log_level="warning",
        reload=True,  # Enable hot-reload for live coding
        reload_dirs=["D:/Desktop/Github_Jarvis"]
    )


def main():
    """Main entry point for J.A.R.V.I.S.
    
    Parses command-line arguments and launches appropriate interface:
    - No args or --desktop: tkinter GUI
    - --web [port]: FastAPI web server
    
    Command-line Arguments:
        --web        Launch web interface (optional port follows)
        --desktop    Launch desktop GUI (default, explicit)
        [port]       Port number for web server (must follow --web)
    
    Examples:
        python jarvis.py              # Desktop GUI
        python jarvis.py --desktop    # Desktop GUI (explicit)
        python jarvis.py --web        # Web UI on port 4444
        python jarvis.py --web 8000   # Web UI on port 8000
    """
    # Check for --web flag in command-line arguments
    if "--web" in sys.argv:
        web_index = sys.argv.index("--web")
        
        # Check if a port number follows the --web flag
        port = 4444  # Default port
        if web_index + 1 < len(sys.argv):
            next_arg = sys.argv[web_index + 1]
            # Verify the next argument is a valid port number
            if next_arg.isdigit():
                port = int(next_arg)
        
        run_web(port)
    else:
        # Default to desktop mode
        run_desktop()


if __name__ == "__main__":
    main()