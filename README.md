# J.A.R.V.I.S.

**Just A Rather Very Intelligent System** — A powerful voice-controlled AI assistant with both desktop and web interfaces.

## Overview

J.A.R.V.I.S. is a comprehensive AI assistant built on the **fury-sdk** framework, providing:

- **Voice Control**: Natural language input/output with speech recognition and synthesis
- **Desktop Interface**: Beautiful tkinter-based holographic GUI
- **Web Interface**: Browser-based control panel (http://localhost:4444)
- **Extensive Tool Suite**: 20+ specialized tools for productivity and system control

## Features

### Core Capabilities
- Voice input (STT) and voice output (TTS)
- Multi-turn conversations with memory persistence
- Real-time screen capture and image analysis
- System automation and control

### Tool Suite
- **Browser Tools**: Web automation and navigation
- **Calendar Tools**: Schedule management
- **Email**: Gmail integration with token authentication
- **File System**: Advanced file operations
- **Keyboard & Mouse**: System input automation
- **Screenshot & Camera**: Visual input capture
- **News & Web Search**: Information retrieval
- **System Tools**: Process and performance monitoring
- **Media Control**: Volume, audio, video management
- **And more**: Clipboard, timer, notes, learning tools

### Interfaces
| Interface | Command | Usage |
|-----------|---------|-------|
| Desktop GUI | `python jarvis.py` | Holographic tkinter interface |
| Web Interface | `python jarvis.py --web` | Browser-based at http://localhost:4444 |
| Backend Only | `python backend.py` | Headless mode |

## Installation

### Requirements
- Python 3.9+
- Windows (primary OS support)
- NVIDIA GPU recommended (CUDA support for faster transcription)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Github_Jarvis.git
   cd Github_Jarvis
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

4. **Configure API keys** (optional)
   - Create a `.env` file in the project root
   - Add your API keys for various services (Gmail, weather, etc.)

5. **Run**
   ```bash
   # Desktop interface
   python jarvis.py
   
   # Web interface
   python jarvis.py --web
   ```

## Configuration

The system uses environment variables for configuration:

- `FURY_API_KEY`: API key for fury-sdk services
- `WEATHER_API_KEY`: Optional weather service API key
- Google credentials files are stored in `credentials.json` and `gmail_token.json`

See `.env.example` for available configuration options.

## Architecture

```
├── jarvis.py           # Entry point (desktop & web modes)
├── backend.py          # Async backend with fury integration
├── gui.py              # Desktop interface (tkinter)
├── web_server.py       # FastAPI web interface
├── web/                # Frontend assets
└── tools/              # 20+ specialized tool modules
```

### Key Components

- **Backend**: Asyncio-based agent running in daemon thread with fury-sdk
- **GUI**: Real-time voice visualization and command interface
- **Web Server**: FastAPI endpoint for browser control
- **Tools**: Modular, extensible tool suite for specific domains

## Usage Examples

### Desktop Mode
```bash
python jarvis.py
```
Launch the holographic desktop interface. Speak or type commands naturally.

### Web Mode
```bash
python jarvis.py --web
```
Access via browser at `http://localhost:4444`

### Custom Port
```python
from web_server import app
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Performance Optimization

- **GPU Acceleration**: Uses CUDA for Whisper-based speech recognition (float16)
- **Async Processing**: Non-blocking operations for responsive UI
- **OpenAI Compatibility**: Strips incompatible parameters for API compatibility

## Dependencies

See `requirements.txt` for complete list. Key packages:
- `fury-sdk[voice,tts]` - Core AI framework
- `fastapi` + `uvicorn` - Web server
- `pyautogui` - System automation
- `Pillow` - Image processing
- `httpx` - HTTP requests
- `python-dotenv` - Environment configuration

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Author

Created and maintained by the community.

---

**Note**: This project handles system-level operations. Use responsibly and ensure you understand the implications of each automation tool before using in production environments.
