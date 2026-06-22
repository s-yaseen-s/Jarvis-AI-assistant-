# Contributing to J.A.R.V.I.S.

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the J.A.R.V.I.S. project.

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and respect our Code of Conduct:

- Be respectful and inclusive
- Welcome diverse perspectives
- Focus on constructive feedback
- Report violations to the maintainers

## Getting Started

### Prerequisites
- Python 3.9 or higher
- Git and GitHub account
- Familiarity with asyncio, FastAPI, and tkinter (depending on area)

### Development Setup

1. **Fork the repository**
   ```bash
   # On GitHub, click "Fork"
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR-USERNAME/Jarvis-AI-assistant.git
   cd Jarvis-AI-assistant
   ```

3. **Create a virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

6. **Set up your .env**
   ```bash
   cp .env.example .env
   # Add your API keys to .env
   ```

## Types of Contributions

### 1. Bug Reports 🐛
If you find a bug, please open an issue with:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, Python version, etc.)
- Error messages/logs

**Example**:
```
Title: Voice input fails on Windows 11 with certain microphones

Description:
When using a USB microphone, voice input throws an error...

Steps to reproduce:
1. Connect USB microphone
2. Click listen button
3. Speak for 5 seconds

Expected: Audio is transcribed
Actual: Error message appears

Environment:
- Windows 11 22H2
- Python 3.10
- sounddevice 0.4.6
```

### 2. Feature Requests 💡
Suggest new features with:
- Clear description of the feature
- Use cases and benefits
- Possible implementation approach
- Any related issues/PRs

**Example**:
```
Title: Add support for local Ollama models

Description:
Allow using local LLMs via Ollama instead of just OpenAI...

Benefits:
- Privacy (no cloud calls)
- Cost reduction
- Offline capability

Implementation:
Could add conditional backend initialization based on LLM_PROVIDER env var
```

### 3. Code Contributions 🔧
Contributions should include:
- Code changes
- Tests (if applicable)
- Documentation updates
- Descriptive commit messages

## Code Standards

### Python Code Style
- Follow [PEP 8](https://pep8.org/)
- Use type hints for function parameters
- Write docstrings for all functions (Google-style)
- Maximum line length: 100 characters (practical limit)

**Example**:
```python
def process_audio(audio_data: bytes, sample_rate: int) -> str:
    """Transcribe audio to text using Whisper STT.
    
    Args:
        audio_data: Raw audio bytes
        sample_rate: Sample rate in Hz (e.g., 16000)
        
    Returns:
        Transcribed text
        
    Raises:
        ValueError: If audio_data is empty
        ImportError: If whisper not installed
    """
    if not audio_data:
        raise ValueError("audio_data cannot be empty")
    
    # Implementation here
    return transcription
```

### Git Commit Messages
Write clear, descriptive commit messages:

```
feat: Add GPU acceleration for speech recognition

- Use faster-whisper library for 7-9x speedup
- Add CUDA support with float16 precision
- Implement fallback to CPU if CUDA unavailable
- Add GPU_DEVICE configuration option

Fixes: #42
```

**Format**:
- **Type**: feat | fix | docs | style | refactor | test | chore
- **Scope**: Optional (feature/component affected)
- **Subject**: 50 characters max, imperative mood
- **Body**: Explain what and why, not how
- **Footer**: Reference related issues/PRs

### Tools Code
When adding new tools:

1. **Create in `tools/your_tools.py`**
2. **Follow the factory pattern**
3. **Include comprehensive docstrings**
4. **Define JSON schemas for input/output**
5. **Handle errors gracefully**
6. **Test with actual backend**

**Example**:
```python
def my_tool_factory():
    """Create a tool for doing something.
    
    Returns:
        Fury tool object
    """
    def my_tool(param: str) -> dict:
        """Execute the tool.
        
        Args:
            param: Input parameter
            
        Returns:
            Dict with success status and result
        """
        try:
            result = do_something(param)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return create_tool(
        id="my_tool",
        description="What this tool does",
        execute=my_tool,
        input_schema={
            "type": "object",
            "properties": {
                "param": {"type": "string", "description": "Input param"}
            },
            "required": ["param"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "result": {"type": "string"},
            },
            "required": ["success"],
        },
    )
```

## Testing

### Running Tests
```bash
python -m pytest tests/
```

### Writing Tests
- Use pytest framework
- Name test files `test_*.py`
- Use descriptive test names
- Aim for >80% code coverage
- Test both success and failure cases

**Example**:
```python
import pytest
from backend import JarvisBackend

def test_backend_starts_successfully():
    """Test that backend initializes without errors."""
    iq = queue.Queue()
    oq = queue.Queue()
    backend = JarvisBackend(iq, oq)
    backend.start()
    
    # Wait for initialization
    assert backend._agent is not None

def test_invalid_api_key_raises_error():
    """Test that missing API key is handled gracefully."""
    with pytest.raises(ValueError):
        backend = JarvisBackend(iq, oq)
        # Should fail with invalid/missing API key
```

## Documentation

### Update Docs For:
- New features (README.md)
- API changes (API.md if exists)
- Architecture changes (ARCHITECTURE.md)
- Setup changes (.env.example, README.md)

### Documentation Format
- Use Markdown
- Keep lines ≤ 80 characters
- Include code examples
- Cross-reference related docs

## Pull Request Process

1. **Before submitting**
   - Ensure code passes linting (if configured)
   - Run tests locally
   - Update documentation
   - Sync with main branch

2. **Create Pull Request**
   - Use descriptive title
   - Reference related issues (#42)
   - Explain changes in detail
   - List any breaking changes

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes
   
   Fixes #42
   
   ## Changes
   - Change 1
   - Change 2
   
   ## Testing
   How to test these changes:
   1. Step 1
   2. Step 2
   
   ## Checklist
   - [ ] Tests pass
   - [ ] Documentation updated
   - [ ] No breaking changes
   - [ ] Code follows style guide
   ```

4. **Review Process**
   - Maintainers will review
   - May request changes
   - Once approved, will merge
   - CI/CD pipeline must pass

## Areas for Contribution

### High Priority
- [ ] Cross-platform support (macOS, Linux)
- [ ] Unit test coverage
- [ ] Performance improvements
- [ ] Bug fixes (open issues)

### Medium Priority
- [ ] New tool implementations
- [ ] Documentation improvements
- [ ] Code refactoring
- [ ] Feature requests

### Lower Priority
- [ ] UI enhancements
- [ ] Code style improvements
- [ ] Example scripts
- [ ] Translations

## Recognition

Contributors will be:
- Added to CONTRIBUTORS.md
- Mentioned in release notes
- Credited in project documentation

## Questions?

- Check existing issues/discussions
- Open a new discussion for questions
- Email maintainers for private concerns

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to J.A.R.V.I.S.! 🚀
