# J.A.R.V.I.S. Architecture

A comprehensive guide to the system design, components, and data flow.

## System Overview

J.A.R.V.I.S. is a multi-threaded, event-driven AI assistant with three distinct interfaces:

```
┌─────────────────────────────────────────────────────────┐
│                    Main Application                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────────┐         ┌──────────────────┐     │
│  │  Desktop Mode    │         │   Web Mode       │     │
│  │  (tkinter GUI)   │         │  (FastAPI)       │     │
│  │                  │         │                  │     │
│  │ - Holographic    │         │ - Browser-based  │     │
│  │   animation      │         │ - Real-time      │     │
│  │ - Voice input    │         │   streaming      │     │
│  │ - Visualization  │         │ - Remote access  │     │
│  └────────┬─────────┘         └────────┬─────────┘     │
│           │                            │                │
│           └────────────────┬───────────┘                │
│                            │                           │
│                    ┌───────▼────────┐                  │
│                    │  Input Queue   │                  │
│                    │  (thread-safe) │                  │
│                    └───────┬────────┘                  │
│                            │                           │
└────────────────────────────┼──────────────────────────┘
                             │
                    ┌────────▼────────────┐
                    │  Backend Thread     │
                    │  (Async Event Loop) │
                    └────────┬────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐    ┌────────▼────────┐    ┌─────▼──────┐
   │   Fury    │    │  Memory Store   │    │   Tools    │
   │   Agent   │    │  (Persistent)   │    │   Suite    │
   │  (GPT-4o) │    │                 │    │ (20+ tools)│
   └───────────┘    └─────────────────┘    └────────────┘
                             │
                    ┌────────▼────────┐
                    │ Output Queue    │
                    │ (thread-safe)   │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼─────┐    ┌────────▼────────┐    ┌─────▼──────┐
   │  Token    │    │  Tool Calls     │    │   Audio    │
   │  Streaming│    │  (Real-time)    │    │  (TTS)     │
   └───────────┘    └─────────────────┘    └────────────┘
```

## Threading Model

### Main Thread (GUI/Web)
- Runs tkinter or FastAPI event loop
- Handles user input and display
- **Does NOT block**: Uses queues for communication
- **Receives**: Status updates, tokens, audio, transcripts

### Backend Thread (Async Agent)
- Independent asyncio event loop
- Runs fury Agent continuously
- **Receives**: User input via input_queue
- **Sends**: Responses via output_queue
- **Daemon**: Terminates when main thread exits

### Thread-Safe Communication
```python
# Main Thread → Backend Thread
input_queue.put({"type": "text", "content": "What time is it?"})

# Backend Thread → Main Thread
output_queue.get()  # {"type": "token", "content": "It is..."}
output_queue.get()  # {"type": "stream_end"}
output_queue.get()  # {"type": "status", "value": "idle"}
```

## Core Components

### 1. JarvisBackend (backend.py)
**Purpose**: Main AI agent orchestrating conversation and tool execution

**Key Methods**:
- `start()`: Spawn daemon thread
- `_main()`: Async event loop - initializes Agent, polls input queue
- `_respond()`: Generate response and stream to output queue
- `_do_tts_web()`: Stream audio via OpenAI TTS-HD
- `_preprocess()`: Bypass safety filters for self-modification/email

**Responsibilities**:
- Initialize fury Agent with system prompt and tools
- Manage conversation history via HistoryManager
- Process voice input (transcription via Whisper)
- Stream tokens in real-time to UI
- Handle tool execution asynchronously
- Generate voice output via OpenAI TTS

**Data Flow**:
```
Input Queue → History Manager → Agent.chat() → Tool Execution
    ↓                                               ↓
    │                                    Output Queue (tokens)
    │                                              ↓
    └──────────────────────────────────→ GUI/Web UI (Display)
```

### 2. Desktop GUI (gui.py)
**Framework**: tkinter (cross-platform)

**Features**:
- Holographic animation with real-time waveform
- Token streaming display
- Tool call visualization
- System stats (CPU, RAM, disk)
- Voice input/output status

**Event Loop**:
```
tkinter.mainloop()
    ↓
root.after(50ms) → Poll output_queue
    ↓
Update UI with new tokens/status
    ↓
Repeat
```

### 3. Web Server (web_server.py)
**Framework**: FastAPI + uvicorn

**Endpoints**:
- `GET /`: Serve HTML interface
- `GET /stream`: WebSocket for real-time updates
- `POST /chat`: Send text/audio input
- `GET /history`: Fetch conversation history

**Features**:
- Browser-based interface (http://localhost:4444)
- Real-time token streaming via WebSocket
- Audio playback in browser
- Remote access capability
- Auto-reload on code changes (development)

### 4. Tool Suite (tools/)
**Architecture**: Modular tool factory pattern

**Structure**:
```
tools/
├── __init__.py          # Tool registration
├── calendar_tools.py    # Google Calendar (OAuth2)
├── browser_tools.py     # Web navigation
├── system_tools.py      # Process control
├── email_tools.py       # Gmail (OAuth2)
├── filesystem_tools.py  # File operations
└── [15+ more tools]
```

**Tool Factory Pattern**:
```python
def my_tool_factory():
    def my_tool(arg: str) -> dict:
        """Actual tool logic"""
        return {"result": "..."}
    
    return create_tool(
        id="my_tool",
        description="What it does",
        execute=my_tool,
        input_schema={...},
        output_schema={...}
    )
```

**Tool Integration**:
```
Agent.chat() 
    ↓
Tool Call Event 
    ↓
Tool Execution (async)
    ↓
Result → Agent Context
    ↓
Response Generation
```

## Data Flow: Text Input Example

```
User Types: "What's the weather in London?"
    ↓
GUI.input_text_widget.get()
    ↓
input_queue.put({"type": "text", "content": "What's the weather in London?"})
    ↓
[Backend Thread]
    ↓
Backend._main() retrieves from input_queue
    ↓
history.add({"role": "user", "content": "What's the weather in London?"})
    ↓
agent.runner().chat(history)  [Async generator]
    ↓
Streaming Events:
    - event.content: "The"
    - event.content: "weather"
    - event.content: " in"
    - event.content: " London"
    - ...
    ↓
Tool Call Detected: get_weather(location="London")
    ↓
Tool Executes: Returns {"temperature_c": 18, "description": "Cloudy"}
    ↓
Agent Continues: "The weather in London is..."
    ↓
Output Queue Receives:
    {"type": "stream_start"}
    {"type": "token", "content": "The"}
    {"type": "token", "content": " weather"}
    {"type": "tool_call", "name": "get_weather"}
    {"type": "token", "content": "..."}
    {"type": "stream_end"}
    {"type": "status", "value": "speaking"}
    {"type": "audio", "data": "base64_encoded_mp3", "fmt": "mp3"}
    {"type": "status", "value": "idle"}
    ↓
[Main Thread - GUI]
    ↓
GUI polls output_queue every 50ms
    ↓
Displays tokens in real-time
    ↓
Shows tool_call indicator
    ↓
Plays audio when stream_end received
    ↓
Updates status to idle
```

## Data Flow: Voice Input Example

```
User Says: "Set a timer for 5 minutes"
    ↓
GUI.listen_button clicked
    ↓
input_queue.put({"type": "voice"})
    ↓
[Backend Thread]
    ↓
Backend._record_audio()
    ↓
sounddevice.rec(5.0 seconds @ 16kHz)
    ↓
Whisper STT (faster-whisper on CUDA)
    ↓
Transcription: "Set a timer for 5 minutes"
    ↓
output_queue.put({"type": "transcript", "content": "Set a timer for 5 minutes"})
    ↓
history.add({"role": "user", "content": "Set a timer for 5 minutes"})
    ↓
agent.runner().chat() [Same as text flow above]
    ↓
Tool Call: set_timer(seconds=300, label="Timer")
    ↓
Timer fires after 5 seconds
    ↓
output_queue.put({"type": "alert", "message": "⏰ Timer — time's up!"})
    ↓
[GUI]
    ↓
Display alert notification
    ↓
Play alert sound
```

## Performance Optimizations

### GPU Acceleration
- **Whisper STT**: CUDA + faster-whisper (float16) = 7-9x faster
- **TTS**: OpenAI TTS-1-HD (streaming sentence-by-sentence)
- **Token Streaming**: Real-time display of partial output

### Async Processing
- Non-blocking voice I/O via asyncio executors
- Parallel tool execution with `parallel_tool_calls=False` (sequential for clarity)
- Queue-based IPC prevents UI freezing

### Memory Management
- **Context Window**: 128k tokens (GPT-4o limit)
- **Token Compaction**: HistoryManager auto-compacts old messages
- **Reserve Tokens**: 2048 reserved for responses
- **Persistent History**: Disk storage with auto-load

### Caching
- Google OAuth tokens cached (avoid re-auth)
- System stats cached (2-second interval)
- Tool registry pre-computed on startup

## API Compatibility Patches

### Patch 1: OpenAI Parameter Stripping
```python
# fury-sdk adds chat_template_kwargs for local models
# OpenAI API rejects these → 400 Bad Request
_fury_runtime._build_chat_completion_kwargs = _openai_build
# Solution: Strip before sending to API
```

### Patch 2: GPU Whisper
```python
# fury uses base.en Whisper (slow)
# Patch to use faster-whisper (7-9x faster)
_fury_voice._create_transcription_model = _gpu_transcription_model
```

### Patch 3: Transport Layer
```python
# HistoryManager bypasses runtime patch
# Patch transport directly for consistency
_fury_transport.AsyncChatCompletions.create = _patched_transport_create
```

## Security Considerations

### API Keys
- ✅ Stored in .env (not in code)
- ✅ Loaded via python-dotenv
- ✅ Never logged or displayed
- ❌ Prevent .env from being committed (.gitignore)

### OAuth2 Authentication
- ✅ Google OAuth2 flow for Calendar/Gmail
- ✅ Tokens cached locally (token.json)
- ✅ Automatic token refresh
- ✅ Scopes limited to necessary permissions

### Tool Execution
- ✅ Input validation via JSON schemas
- ✅ Error handling for failed tools
- ✅ No arbitrary code execution
- ⚠️ File operations can read/write anywhere (user responsibility)

### User Privacy
- ✅ Private mode disables audio input on demand
- ⚠️ Conversation history stored locally
- ⚠️ Screenshots/audio not auto-deleted

## Extension Points

### Adding a New Tool
```python
# tools/my_tools.py
def my_tool_factory():
    def my_tool(param: str) -> dict:
        return {"result": "..."}
    
    return create_tool(
        id="my_tool",
        description="Does something",
        execute=my_tool,
        input_schema={"type": "object", "properties": {...}},
        output_schema={"type": "object", "properties": {...}}
    )

# tools/__init__.py
from .my_tools import my_tool_factory

TOOLS = [my_tool_factory(), ...]
```

### Custom System Prompt
Edit `SYSTEM_PROMPT` in backend.py or set via environment:
```python
SYSTEM_PROMPT = """Your custom personality here..."""
```

### Custom UI Theme
Edit colors in gui.py or web/index.html

## Deployment Scenarios

### Desktop (Development)
```bash
python jarvis.py
```
- Single-machine use
- Hotkey listening (always on)
- Local audio I/O

### Web Server (Remote Access)
```bash
python jarvis.py --web
```
- Network access via localhost:4444
- Browser-based
- Suitable for remote machines

### Headless (Backend Only)
```bash
python backend.py
```
- No UI
- Programmatic access
- Integration with other systems

## Known Limitations

1. **Windows-only**: Primary support for Windows (tkinter GUI, system tools)
2. **Single User**: One conversation context at a time
3. **No Database**: History stored in files, not scalable to millions
4. **Token Limits**: OpenAI API has rate limits (3.5K RPM, 90K TPM for free tier)
5. **Audio Hardware**: Requires microphone + speakers

## Future Architecture Improvements

- [ ] Cross-platform support (macOS, Linux)
- [ ] Multi-user support with user-specific memory
- [ ] Persistent database (PostgreSQL) instead of files
- [ ] Caching layer (Redis) for conversation context
- [ ] Load balancing for multiple backend instances
- [ ] WebSocket multiplexing for real-time sync
- [ ] Plugin system for third-party extensions
