# J.A.R.V.I.S. — Voice-Controlled AI Assistant

**Just A Rather Very Intelligent System** — A production-grade voice-controlled AI assistant with dual interfaces, 20+ integrated tools, and GPU acceleration.

[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)](https://fastapi.tiangolo.com/)
[![GPT-4o](https://img.shields.io/badge/GPT--4o-OpenAI-412991)](https://openai.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎥 Live Demo

### Desktop Interface — Holographic Core Reactor

![J.A.R.V.I.S. Desktop GUI](https://github.com/s-yaseen-s/Jarvis-AI-assistant-/raw/main/demo/demo-desktop.png)

**Features Shown:**
- ✨ Holographic animated waveform visualization
- 💬 Real-time conversation log with timestamps
- 📊 System diagnostics dashboard (CPU, RAM, Disk)
- 🔊 Audio analysis waveform display
- 🎨 Professional dark-themed UI with cyan accents

### Web Interface — Neural Network Dashboard

![J.A.R.V.I.S. Web Dashboard](https://github.com/s-yaseen-s/Jarvis-AI-assistant-/raw/main/demo/demo-web.png)

**Features Shown:**
- 🧠 3D neural network visualization (rotating mesh)
- 📈 Real-time system metrics (CPU, Memory, Services)
- 💬 Active conversation tracking with full dialogue
- 🔍 Service status monitoring (OpenAI API, STT, TTS, GPU)
- 🎛️ Control panel (Power, Mic, Camera, Screen, Private, Chat, Terminal, Apps)

---

## ✨ Core Features

### Voice & Input
- 🎙️ **Real-time Speech Recognition** - faster-whisper on CUDA (7-9x faster)
- 🔊 **Natural Speech Output** - OpenAI TTS-HD with streaming
- 📝 **Transcription Display** - Live transcript of voice commands
- 🎯 **Dual Input Methods** - Voice or text

### Intelligence
- 🧠 **GPT-4o Integration** - State-of-the-art language model
- 💾 **Persistent Memory** - 128k token context window with auto-compaction
- 🔄 **Multi-turn Conversations** - Full conversation history management
- 🎭 **Custom Personality** - J.A.R.V.I.S. persona with dry wit

### Tool Suite (20+)
**Communication:** Gmail, Google Calendar, Clipboard

**Information & Web:** Web Search, News, Weather, Page Fetching, YouTube, Google

**System & Automation:** Process Management, Shell Commands, File System, Volume Control, Keyboard/Mouse

**Visual I/O:** Screenshots, Webcam, Vision Analysis, Screen Reading

**Productivity:** Timer, Notes, Reflections, Skills

### Interfaces
| Interface | Access | Best For |
|-----------|--------|----------|
| **Desktop** | `python jarvis.py` | Local, interactive use |
| **Web** | `python jarvis.py --web` | Remote, browser-based |
| **Headless** | `python backend.py` | Integration |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- Windows OS
- OpenAI API key
- 4GB+ RAM (GPU recommended)

### Installation

1. **Clone the repository**
```bash
   git clone https://github.com/s-yaseen-s/Jarvis-AI-assistant-.git
   cd Jarvis-AI-assistant-
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

4. **Configure API keys**
```bash
   cp .env.example .env
   # Edit .env and add: OPENAI_API_KEY=sk-proj-your-key-here
```

5. **Run the assistant**
```bash
   # Desktop interface
   python jarvis.py
   
   # Web interface
   python jarvis.py --web
```

---

## 🏗️ Architecture

Voice Input → Whisper STT → GPT-4o Agent → 20+ Tools → Response

↓                                                      ↓

Desktop GUI / Web UI ← Token Streaming ← TTS Output

---

## 🛠️ Technology Stack

- **Backend:** Python, asyncio, fury-sdk, FastAPI
- **AI/ML:** GPT-4o, faster-whisper, OpenAI TTS-HD, CUDA
- **Desktop:** tkinter, numpy, sounddevice
- **Web:** FastAPI, uvicorn, WebSocket
- **APIs:** Google Calendar, Gmail, DuckDuckGo

---

## 📊 Project Statistics

- **14 Commits** - Thoughtful incremental development
- **20+ Tools** - Across 8 categories
- **128k Token Context** - GPT-4o capability
- **7-9x Faster STT** - GPU acceleration
- **Production-Ready** - Comprehensive documentation

---

## 📚 Documentation

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design deep dive
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[CHANGELOG.md](CHANGELOG.md)** - Version history & roadmap
- **[.env.example](.env.example)** - Configuration template

---

## 📜 License

MIT License — see [LICENSE](LICENSE)

---

## 👤 Author

**Yaseen Mohammed Bilal**

- 📧 Email: s-yaseen.bilal@zewailcity.edu.eg
- 🔗 LinkedIn: [yaseen-mohammed-bilal-6979553b0](https://www.linkedin.com/in/yaseen-mohammed-bilal-6979553b0)
- 💻 GitHub: [@s-yaseen-s](https://github.com/s-yaseen-s)

---

<p align="center">
  <i>Always learning. Always shipping. Always improving.</i>
</p>