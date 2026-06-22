"""
J.A.R.V.I.S. — Holographic Interface
"""

import math
import queue
import random
import tkinter as tk
from datetime import datetime

# ── Colour palette ──────────────────────────────────────────────────────────
BG        = "#000810"
BG_PANEL  = "#000d1a"
BG_ENTRY  = "#001122"
CYAN      = "#00e5ff"
CYAN_MID  = "#00aacc"
CYAN_DIM  = "#003344"
BLUE      = "#0044aa"
TEXT      = "#b8eeff"
TEXT_DIM  = "#446688"
WHITE     = "#e8f8ff"
GREEN     = "#00ff88"
ORANGE    = "#ff7700"
RED       = "#ff3333"
BORDER    = "#002233"

FONT      = ("Consolas", 11)
FONT_SM   = ("Consolas", 9)
FONT_LG   = ("Consolas", 13, "bold")
FONT_HUD  = ("Consolas", 10)
FONT_TITLE = ("Consolas", 24, "bold")


# ── Reusable holographic container ──────────────────────────────────────────

def holo_frame(parent, title="", pad=8, **kw):
    """Create a holographic container with cyan border and title.
    
    Returns a tuple of (outer_frame, inner_frame) where outer has the border
    and title, and inner is the usable content area.
    
    Args:
        parent: Parent tkinter widget
        title: Optional title text for the frame header
        pad: Padding inside the frame (default: 8)
        **kw: Additional keyword arguments passed to outer frame
        
    Returns:
        Tuple of (outer_frame, inner_frame)
    """
    outer = tk.Frame(parent, bg=BORDER, **kw)
    if title:
        tk.Label(outer, text=f" {title} ", font=FONT_SM,
                 fg=CYAN_MID, bg=BORDER, anchor="w", padx=4
                 ).pack(fill="x", side="top")
    inner = tk.Frame(outer, bg=BG_PANEL, padx=pad, pady=pad - 2)
    inner.pack(fill="both", expand=True, padx=1, pady=(0, 1))
    return outer, inner


# ── Arc reactor ─────────────────────────────────────────────────────────────

class ArcReactor(tk.Canvas):
    """Animated concentric-ring reactor graphic.
    
    Displays a continuously rotating multi-ring reactor with glowing core,
    mimicking the arc reactor from Iron Man.
    """

    def __init__(self, parent, size=188, **kw):
        """Initialize the arc reactor animation.
        
        Args:
            parent: Parent tkinter widget
            size: Size of the reactor in pixels (default: 188)
            **kw: Additional keyword arguments passed to Canvas
        """
        super().__init__(parent, width=size, height=size,
                         bg=BG_PANEL, highlightthickness=0, **kw)
        self.s  = size
        self.cx = size / 2
        self.cy = size / 2
        self.r1 = 0.0   # outer ring rotation
        self.r2 = 0.0   # inner ring counter-rotation
        self.ph = 0.0   # pulse phase
        self._tick()

    def _tick(self):
        """Update and redraw the reactor animation frame."""
        self.delete("all")
        cx, cy, s = self.cx, self.cy, self.s
        pulse = (math.sin(self.ph) + 1) / 2  # 0 → 1

        # — outermost segmented ring —
        ro = s * 0.455
        for i in range(16):
            a   = self.r1 + i * 22.5
            col = CYAN if i % 4 == 0 else (CYAN_MID if i % 2 == 0 else CYAN_DIM)
            self.create_arc(cx - ro, cy - ro, cx + ro, cy + ro,
                            start=a, extent=15, style="arc",
                            outline=col, width=2 if i % 4 == 0 else 1)

        # — counter-rotating middle ring —
        rm = s * 0.34
        for i in range(8):
            a = -self.r2 + i * 45
            self.create_arc(cx - rm, cy - rm, cx + rm, cy + rm,
                            start=a, extent=28, style="arc",
                            outline=CYAN_MID, width=2)

        # — tick marks on middle ring —
        for i in range(36):
            rad  = math.radians(i * 10)
            big  = i % 9 == 0
            ri   = rm - (5 if big else 2)
            ro2  = rm + (5 if big else 2)
            col  = CYAN if big else CYAN_DIM
            self.create_line(
                cx + ri * math.cos(rad), cy - ri * math.sin(rad),
                cx + ro2 * math.cos(rad), cy - ro2 * math.sin(rad),
                fill=col, width=1)

        # — glowing core —
        rc = s * 0.195
        iv = 0.50 + 0.50 * pulse
        gc = f"#00{int(229 * iv):02x}{int(255 * iv):02x}"
        self.create_oval(cx - rc, cy - rc, cx + rc, cy + rc,
                         fill=gc, outline=CYAN, width=2)

        # — inner hexagon —
        hr  = s * 0.115
        pts = []
        for i in range(6):
            a = math.radians(60 * i - 30 + self.r1 * 0.25)
            pts += [cx + hr * math.cos(a), cy - hr * math.sin(a)]
        self.create_polygon(pts, fill=BG_PANEL, outline=CYAN, width=1)

        # — centre dot —
        self.create_oval(cx - 4, cy - 4, cx + 4, cy + 4,
                         fill=CYAN, outline="")

        self.r1  = (self.r1 + 1.6) % 360
        self.r2  = (self.r2 + 1.1) % 360
        self.ph += 0.065
        self.after(45, self._tick)


# ── Audio waveform ───────────────────────────────────────────────────────────

class Waveform(tk.Canvas):
    """Animated equaliser-bar waveform.
    
    Displays a dynamic audio waveform visualization with multiple frequency
    components. Active state shows responsive animation; idle shows gentle pulse.
    """

    def __init__(self, parent, width=214, height=52, **kw):
        """Initialize the waveform animation canvas.
        
        Args:
            parent: Parent tkinter widget
            width: Canvas width in pixels (default: 214)
            height: Canvas height in pixels (default: 52)
            **kw: Additional keyword arguments passed to Canvas
        """
        super().__init__(parent, width=width, height=height,
                         bg=BG_PANEL, highlightthickness=0, **kw)
        self.w      = width
        self.h      = height
        self.ph     = 0.0
        self.active = False
        self._tick()

    def set_active(self, val: bool):
        """Set waveform to active (animated) or idle state.
        
        Args:
            val: True for active animation, False for idle
        """
        self.active = val

    def _tick(self):
        """Update and redraw the waveform animation frame."""
        self.delete("all")
        n  = 44
        bw = self.w / n
        cy = self.h / 2
        for i in range(n):
            if self.active:
                amp = (abs(math.sin(i * 0.44 + self.ph)) * 0.55 +
                       abs(math.sin(i * 0.19 + self.ph * 1.8)) * 0.30 +
                       random.random() * 0.15) * cy * 0.92
            else:
                amp = abs(math.sin(i * 0.33 + self.ph)) * cy * 0.13 + 1.5
            x   = i * bw + bw / 2
            col = CYAN if self.active else CYAN_DIM
            self.create_line(x, cy - amp, x, cy + amp,
                             fill=col, width=max(1, int(bw - 1)))
        self.ph += 0.13
        self.after(46, self._tick)


# ── Progress bar ─────────────────────────────────────────────────────────────

class HoloBar(tk.Frame):
    """A labelled horizontal progress bar.
    
    Displays system metrics (CPU, RAM, disk) with color-coded progress
    and percentage values. Colors change dynamically based on threshold.
    """

    def __init__(self, parent, label="", **kw):
        """Initialize a holographic progress bar.
        
        Args:
            parent: Parent tkinter widget
            label: Label text for the metric (e.g., 'CPU', 'RAM')
            **kw: Additional keyword arguments passed to Frame
        """
        super().__init__(parent, bg=BG_PANEL, **kw)
        tk.Label(self, text=f"{label:<5}", font=FONT_SM,
                 fg=TEXT_DIM, bg=BG_PANEL, width=5, anchor="w"
                 ).pack(side="left")
        track = tk.Frame(self, bg=CYAN_DIM, height=9)
        track.pack(side="left", fill="x", expand=True, padx=4)
        track.pack_propagate(False)
        self._fill = tk.Frame(track, bg=GREEN, height=9)
        self._fill.place(x=0, y=0, relheight=1.0, width=0)
        self._track = track
        self._pct = tk.Label(self, text="0%", font=FONT_SM,
                             fg=TEXT, bg=BG_PANEL, width=5, anchor="e")
        self._pct.pack(side="left")

    def set(self, val: float):
        """Update the progress bar to a specific percentage.
        
        Changes color based on value: green (<60%), orange (60-85%), red (>85%).
        
        Args:
            val: Percentage value (0-100)
        """
        self.update_idletasks()
        w = self._track.winfo_width()
        fw = max(1, int(w * val / 100))
        col = GREEN if val < 60 else (ORANGE if val < 85 else RED)
        self._fill.config(bg=col)
        self._fill.place_configure(width=fw)
        self._pct.config(text=f"{val:.0f}%")


# ── Main UI class ────────────────────────────────────────────────────────────

class JarvisUI:
    """Main UI controller for J.A.R.V.I.S. desktop interface.
    
    Manages the holographic display, conversation log, input/output,
    and real-time system stats. Communicates with backend via queues.
    """

    def __init__(self, root: tk.Tk,
                 iq: queue.Queue,   # GUI → backend
                 oq: queue.Queue):  # backend → GUI
        """Initialize the JARVIS UI.
        
        Args:
            root: Main tkinter window
            iq: Input queue (GUI → backend)
            oq: Output queue (backend → GUI)
        """
        self.root = root
        self.iq   = iq
        self.oq   = oq
        self._streaming = False

        self._setup_window()
        self._build_header()
        self._build_body()
        self._build_input()
        self._poll()

    # ── Window setup ────────────────────────────────────────────

    def _setup_window(self):
        """Configure main window properties and grid layout."""
        r = self.root
        r.title("J.A.R.V.I.S.")
        r.configure(bg=BG)
        r.geometry("1160x780")
        r.minsize(920, 660)
        r.columnconfigure(0, weight=1)
        r.rowconfigure(1, weight=1)

    # ── Header ──────────────────────────────────────────────────

    def _build_header(self):
        """Build the top header with title, status indicator, and clock."""
        hdr = tk.Frame(self.root, bg="#000d20", height=54)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)

        tk.Frame(hdr, bg=CYAN,     height=1).pack(fill="x", side="top")
        tk.Frame(hdr, bg=CYAN_DIM, height=1).pack(fill="x", side="top")

        inner = tk.Frame(hdr, bg="#000d20")
        inner.pack(fill="both", expand=True, padx=14)

        tk.Label(inner, text="J.A.R.V.I.S.", font=FONT_TITLE,
                 fg=CYAN, bg="#000d20").pack(side="left")
        tk.Label(inner, text="JUST A RATHER VERY INTELLIGENT SYSTEM",
                 font=FONT_SM, fg=TEXT_DIM, bg="#000d20").pack(side="left", padx=12)

        right = tk.Frame(inner, bg="#000d20")
        right.pack(side="right")

        self._clock_lbl = tk.Label(right, text="", font=FONT_HUD,
                                   fg=CYAN, bg="#000d20")
        self._clock_lbl.pack(side="right", padx=(10, 0))

        self._status_lbl = tk.Label(right, text="● ONLINE", font=FONT_HUD,
                                    fg=GREEN, bg="#000d20")
        self._status_lbl.pack(side="right", padx=10)

        tk.Frame(hdr, bg=CYAN_DIM, height=1).pack(fill="x", side="bottom")
        self._tick_clock()

    def _tick_clock(self):
        """Update clock display and reschedule next update."""
        self._clock_lbl.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self._tick_clock)

    # ── Body ────────────────────────────────────────────────────

    def _build_body(self):
        """Build the main body panels (left reactor/stats, right conversation)."""
        body = tk.Frame(self.root, bg=BG)
        body.grid(row=1, column=0, sticky="nsew", padx=8, pady=6)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_left(body)
        self._build_right(body)

    # ── Left panel ──────────────────────────────────────────────

    def _build_left(self, parent):
        """Build left panel with arc reactor, waveform, and system diagnostics."""
        left = tk.Frame(parent, bg=BG, width=248)
        left.grid(row=0, column=0, sticky="ns", padx=(0, 7))
        left.pack_propagate(False)
        left.grid_propagate(False)

        # Arc reactor
        out, inn = holo_frame(left, "CORE REACTOR")
        out.pack(fill="x", pady=(0, 5))
        self.reactor = ArcReactor(inn, size=188)
        self.reactor.pack(pady=4)

        # Waveform
        out2, inn2 = holo_frame(left, "AUDIO ANALYSIS")
        out2.pack(fill="x", pady=(0, 5))
        self.waveform = Waveform(inn2, width=214, height=52)
        self.waveform.pack(pady=3)

        # Status / mode block
        out3, inn3 = holo_frame(left, "OPERATIONAL STATUS")
        out3.pack(fill="x", pady=(0, 5))
        self._mode_lbl = tk.Label(inn3, text="INITIALIZING",
                                  font=("Consolas", 14, "bold"),
                                  fg=CYAN_MID, bg=BG_PANEL)
        self._mode_lbl.pack(pady=(4, 0))
        self._tool_lbl = tk.Label(inn3, text="",
                                  font=FONT_SM, fg=ORANGE, bg=BG_PANEL,
                                  wraplength=210, justify="left")
        self._tool_lbl.pack(pady=(2, 6))

        # Mini stats
        out4, inn4 = holo_frame(left, "DIAGNOSTICS")
        out4.pack(fill="x")
        self._bars = {}
        for metric in ("CPU", "RAM", "DISK"):
            b = HoloBar(inn4, label=metric)
            b.pack(fill="x", pady=2)
            self._bars[metric] = b

    # ── Right panel ─────────────────────────────────────────────

    def _build_right(self, parent):
        """Build right panel with conversation log and message display."""
        right = tk.Frame(parent, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # Conversation log
        out, inn = holo_frame(right, "CONVERSATION LOG", pad=4)
        out.grid(row=1, column=0, sticky="nsew")

        self._conv = tk.Text(
            inn, bg=BG_PANEL, fg=TEXT,
            font=FONT, insertbackground=CYAN,
            wrap="word", relief="flat", bd=0,
            state="disabled", cursor="arrow",
            spacing1=2, spacing3=2,
        )
        sb = tk.Scrollbar(inn, command=self._conv.yview,
                          bg=BG_PANEL, troughcolor=BORDER,
                          activebackground=CYAN_MID, relief="flat",
                          width=10)
        self._conv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._conv.pack(side="left", fill="both", expand=True)

        self._conv.tag_configure("ts",     foreground=TEXT_DIM,  font=FONT_SM)
        self._conv.tag_configure("jarvis", foreground=CYAN,      font=("Consolas", 11, "bold"))
        self._conv.tag_configure("user",   foreground=WHITE,     font=("Consolas", 11, "bold"))
        self._conv.tag_configure("body",   foreground=TEXT)
        self._conv.tag_configure("tool",   foreground=ORANGE,    font=FONT_SM)
        self._conv.tag_configure("alert",  foreground=GREEN,     font=("Consolas", 11, "bold"))
        self._conv.tag_configure("err",    foreground=RED,       font=FONT_SM)

        self._conv_append("JARVIS", "All systems online. Good day, sir.", "jarvis")

    # ── Conversation helpers ─────────────────────────────────────

    def _conv_append(self, sender: str, text: str, tag: str):
        """Append a complete message to conversation log.
        
        Args:
            sender: Who sent the message ('YOU', 'JARVIS', 'ALERT', etc.)
            text: Message content
            tag: Color tag for styling
        """
        self._conv.config(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self._conv.insert("end", f"\n[{ts}] ", "ts")
        self._conv.insert("end", f"{sender} › ", tag)
        self._conv.insert("end", text, "body")
        self._conv.config(state="disabled")
        self._conv.see("end")

    def _conv_start_jarvis(self):
        """Start a new JARVIS response in the conversation log."""
        self._conv.config(state="normal")
        ts = datetime.now().strftime("%H:%M:%S")
        self._conv.insert("end", f"\n[{ts}] ", "ts")
        self._conv.insert("end", "JARVIS › ", "jarvis")
        self._conv.config(state="disabled")
        self._conv.see("end")

    def _conv_token(self, token: str):
        """Append a single token to the current JARVIS response.
        
        Args:
            token: Text token to append
        """
        self._conv.config(state="normal")
        self._conv.insert("end", token, "body")
        self._conv.config(state="disabled")
        self._conv.see("end")

    def _conv_tool(self, name: str):
        """Log a tool call in the conversation.
        
        Args:
            name: Name of the tool being called
        """
        self._conv.config(state="normal")
        self._conv.insert("end", f"\n  ⚙  calling {name}...", "tool")
        self._conv.config(state="disabled")
        self._conv.see("end")

    # ── Input bar ────────────────────────────────────────────────

    def _build_input(self):
        """Build input bar with microphone button, text entry, and send button."""
        bar = tk.Frame(self.root, bg="#000d20", height=62)
        bar.grid(row=2, column=0, sticky="ew", padx=8, pady=(0, 8))
        bar.grid_propagate(False)

        tk.Frame(bar, bg=CYAN_DIM, height=1).pack(fill="x", side="top")

        inn = tk.Frame(bar, bg="#000d20")
        inn.pack(fill="both", expand=True, padx=10, pady=8)

        # Mic button
        self._mic_btn = tk.Button(
            inn, text="🎤", font=("Consolas", 14),
            bg=BG_ENTRY, fg=CYAN, activebackground=BLUE,
            activeforeground=WHITE, relief="flat", bd=0,
            padx=10, cursor="hand2",
            command=self._voice_click,
        )
        self._mic_btn.pack(side="left", padx=(0, 8))

        # Entry
        border = tk.Frame(inn, bg=CYAN_DIM, padx=1, pady=1)
        border.pack(side="left", fill="both", expand=True)
        self._entry = tk.Entry(
            border, bg=BG_ENTRY, fg=WHITE,
            font=FONT, insertbackground=CYAN,
            relief="flat", bd=6,
        )
        self._entry.pack(fill="both", expand=True)
        self._entry.bind("<Return>", self._send)
        self._entry.bind("<FocusIn>",  lambda e: border.config(bg=CYAN))
        self._entry.bind("<FocusOut>", lambda e: border.config(bg=CYAN_DIM))
        self._entry.focus_set()

        # Send button
        tk.Button(
            inn, text="SEND ›", font=("Consolas", 10, "bold"),
            bg=BLUE, fg=WHITE, activebackground=CYAN,
            activeforeground=BG, relief="flat", bd=0,
            padx=14, cursor="hand2",
            command=self._send,
        ).pack(side="left", padx=(8, 0))

    def _send(self, _=None):
        """Send the current text input to the backend."""
        text = self._entry.get().strip()
        if not text:
            return
        self._entry.delete(0, "end")
        self._conv_append("YOU", text, "user")
        self.iq.put({"type": "text", "content": text})

    def _voice_click(self):
        """Handle microphone button click to start voice input."""
        self._set_mode("LISTENING")
        self.waveform.set_active(True)
        self.iq.put({"type": "voice"})

    # ── Status helpers ───────────────────────────────────────────

    def _set_mode(self, mode: str):
        """Update the operational status display.
        
        Args:
            mode: Status mode ('IDLE', 'LISTENING', 'THINKING', 'SPEAKING', 'ERROR')
        """
        palette = {
            "IDLE":         (CYAN_MID, "IDLE"),
            "LISTENING":    (GREEN,    "LISTENING"),
            "THINKING":     (ORANGE,   "THINKING"),
            "SPEAKING":     (CYAN,     "SPEAKING"),
            "INITIALIZING": (TEXT_DIM, "INITIALIZING"),
            "ERROR":        (RED,      "ERROR"),
        }
        col, label = palette.get(mode, (TEXT, mode))
        self._mode_lbl.config(text=label, fg=col)

    # ── Queue polling ────────────────────────────────────────────

    def _poll(self):
        """Poll output queue for messages from backend and dispatch them."""
        try:
            while True:
                self._dispatch(self.oq.get_nowait())
        except queue.Empty:
            pass
        self.root.after(38, self._poll)

    def _dispatch(self, msg: dict):
        """Process and display a message from the backend.
        
        Args:
            msg: Message dict with 'type' and associated data
        """
        t = msg.get("type")

        if t == "status":
            s = msg["value"].upper()
            self._set_mode(s)
            self.waveform.set_active(s in ("LISTENING", "SPEAKING"))

        elif t == "transcript":
            self._conv_append("YOU", msg["content"], "user")
            self._set_mode("THINKING")
            self.waveform.set_active(False)

        elif t == "stream_start":
            self._streaming = True
            self._conv_start_jarvis()

        elif t == "token":
            if not self._streaming:
                self._streaming = True
                self._conv_start_jarvis()
            self._conv_token(msg["content"])

        elif t == "stream_end":
            self._streaming = False
            self._tool_lbl.config(text="")

        elif t == "tool_call":
            name = msg["name"]
            self._tool_lbl.config(text=f"⚙  {name}")
            self._conv_tool(name)

        elif t == "stats":
            for k in ("CPU", "RAM", "DISK"):
                self._bars[k].set(msg.get(k.lower(), 0))

        elif t == "alert":
            self._conv_append("ALERT", msg["message"], "alert")

        elif t == "error":
            self._conv_append("ERROR", msg["message"], "err")
            self._set_mode("ERROR")