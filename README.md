# J.A.R.V.I.S. — Voice-Controlled AI Assistant

**Just A Rather Very Intelligent System** — A production-grade voice-controlled AI assistant with dual desktop and web interfaces, 20+ integrated tools, and full system automation capabilities.

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Web%20API-green)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Overview

J.A.R.V.I.S. is a comprehensive, production-ready AI assistant framework built on **fury-sdk**, featuring:

- **🎙️ Voice Control**: Natural language speech recognition (STT) and synthesis (TTS)
- **🖥️ Dual Interfaces**: Beautiful holographic desktop GUI + responsive web dashboard
- **⚡ 20+ Integrated Tools**: Calendar, email, web search, file system, automation, and more
- **🔧 Full System Automation**: Keyboard, mouse, process control, and screen capture
- **🌐 Multi-threaded Architecture**: Async backend with real-time GUI updates
- **📊 Production Ready**: Error handling, logging, environment configuration

---

## ✨ Core Features

### Voice & Input
- Real-time speech-to-text (Whisper-based)
- Natural text-to-speech output
- Keyboard & mouse automation
- Screen and camera capture with vision analysis

### Calendar & Productivity
- Google Calendar integration (create, update, delete events)
- Note-taking with persistent storage
- Timer and reminder system
- Learning tools for skill storage and self-reflection

### Communication
- Gmail integration with full OAuth2 support
- Email search with Gmail syntax
- Clipboard read/write operations
- Browser automation (Google, YouTube search)

### Information & Web
- Real-time web search (DuckDuckGo)
- Weather lookup by location
- News headlines and trending topics
- Full webpage content fetching and parsing

### System Control
- Process and performance monitoring
- Volume and audio control
- File system operations (read, write, delete, move)
- System shell commands with elevation support

### Intelligence
- Multi-turn conversation with memory
- Self-reflection and skill learning
- Private mode (audio suspension)
- Self-modifying code capabilities

---

## 🏗️ Architecture

```
J.A.R.V.I.S./
├── jarvis.py              # Entry point (orchestrates desktop & web modes)
├── backend.py             # Core async agent with fury-sdk integration
├── gui.py                 # Desktop interface (tkinter holographic UI)
├── web_server.py          # FastAPI web server (localhost:4444)
├── web/
│   └── index.html         # Frontend assets
├── tools/                 # 20+ modular tool suite
│   ├── calendar_tools.py       ├─ Gmail, clipboard, filesystem
│   ├── browser_tools.py        ├─ Web search & navigation
│   ├── system_tools.py         ├─ Process & system control
│   ├── learning_tools.py       └─ Skills & self-reflection
│   └── [15+ more tools]
└── resources/             # Assets & configuration
```

### Key Design Patterns

- **Async/Await**: Non-blocking operations with asyncio for responsive UI
- **Tool Factory Pattern**: Each tool is a callable factory returning fury-sdk objects
- **Modular Architecture**: Tools are independently testable and extensible
- **OAuth2 Integration**: Secure Google API authentication with token persistence
- **Error Resilience**: Comprehensive try-catch handling with graceful fallbacks

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Windows OS (primary support)
- 4GB+ RAM (GPU recommended for faster speech recognition)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/s-yaseen-s/Jarvis-AI-assistant.git
   cd Jarvis-AI-assistant
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API keys** (optional but recommended)
   ```bash
   # Create .env file in project root
   echo OPENAI_API_KEY=your_key_here > .env
   echo FURY_API_KEY=your_key_here >> .env
   ```

5. **Run the assistant**
   ```bash
   # Desktop holographic interface
   python jarvis.py
   
   # Web interface (http://localhost:4444)
   python jarvis.py --web
   
   # Headless backend only
   python backend.py
   ```

---

## 📋 Usage Examples

### Desktop Mode
```bash
python jarvis.py
```
Launches the holographic desktop GUI. Speak naturally or type commands:
- *"What's the weather in London?"*
- *"Schedule a meeting tomorrow at 2 PM"*
- *"Search for Python best practices"*
- *"Take a screenshot"*

### Web Mode
```bash
python jarvis.py --web
```
Access the web dashboard at `http://localhost:4444` for remote control and monitoring.

### Programmatic Usage
```python
from backend import JarvisBackend
from fury import Fury

jarvis = JarvisBackend()
jarvis.start()

# Interact via chat interface or API
response = jarvis.process_command("What time is it?")
```

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **AI Framework** | fury-sdk v0.5+ | Voice AI and tool orchestration |
| **Backend** | asyncio, FastAPI | Async processing and web API |
| **Desktop UI** | tkinter | Cross-platform GUI with animations |
| **Web UI** | FastAPI + HTML/JS | Browser-based control panel |
| **Speech** | Whisper API | Speech-to-text transcription |
| **APIs** | Google Calendar, Gmail, OpenAI | Integrated services |
| **Utilities** | httpx, Pillow, pyautogui | HTTP, image, and automation |

---

## 📦 Project Structure & Statistics

```
Language Distribution:
- Python: 71.5% (backend, tools, automation)
- HTML/CSS/JS: 28.5% (web interface)

Code Organization:
- 8 core modules (backend, GUI, web server, etc.)
- 20+ specialized tool modules
- Comprehensive error handling and logging
- Full docstring coverage (Google-style)
```

---

## 🔐 Security & Best Practices

- **OAuth2 Authentication**: Secure Google API access with token management
- **Environment Variables**: API keys stored in `.env`, not in code
- **Error Handling**: Graceful fallbacks and user-friendly error messages
- **Input Validation**: Tool parameters validated against JSON schemas
- **Private Mode**: User can disable audio input for privacy
- **No Hardcoded Credentials**: All sensitive data externalized

---

## 🎓 Learning & Development

This project demonstrates:

✅ **Software Engineering**
- Async/await patterns and event-driven architecture
- RESTful API design (FastAPI)
- Modular, extensible code organization
- Comprehensive error handling and logging

✅ **AI/ML Integration**
- Voice AI and natural language processing
- Third-party API orchestration
- Multi-turn conversation management
- Vision AI for screen analysis

✅ **Full-Stack Development**
- Backend services (Python + asyncio)
- Frontend (HTML/CSS/JavaScript)
- Web frameworks (FastAPI)
- GUI development (tkinter)

✅ **DevOps & Deployment**
- Environment configuration management
- Cross-platform compatibility
- Performance optimization (GPU acceleration)
- Production-ready error handling

---

## 🔧 Configuration

The system respects environment variables for flexibility:

```bash
# API Keys
OPENAI_API_KEY=sk-...
FURY_API_KEY=...

# Google Services (auto-generated on first run)
credentials.json (OAuth2 creds)
token.json (cached tokens)
gmail_token.json (Gmail cache)

# Ports
WEB_PORT=4444 (default)
```

See `.env.example` for complete configuration reference.

---

## 📈 Performance Optimizations

- **GPU Acceleration**: CUDA support for Whisper transcription (float16)
- **Async Processing**: Non-blocking operations prevent UI freezes
- **Lazy Loading**: Tools initialized on-demand, not at startup
- **Caching**: Token and credential caching to reduce API calls
- **Multi-threading**: Background processing with thread pooling

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Yaseen** — Full-stack AI/automation developer
- GitHub: [@s-yaseen-s](https://github.com/s-yaseen-s)
- Project: [Jarvis-AI-assistant](https://github.com/s-yaseen-s/Jarvis-AI-assistant-)

---

## 🎯 Future Enhancements

- [ ] Cross-platform support (macOS, Linux)
- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Customizable voice personas
- [ ] Plugin system for third-party tools
- [ ] Cloud deployment templates
- [ ] Mobile app companion

---

**Made with ❤️ for productivity and automation**