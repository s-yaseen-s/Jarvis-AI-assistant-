"""Self-modification tool — lets JARVIS edit his own source files via a single tool call."""

import os
import re
from pathlib import Path
from fury import create_tool

ROOT = Path("D:/Desktop/Github_Jarvis")

EDITABLE = {
    "backend.py":        ROOT / "backend.py",
    "web_server.py":     ROOT / "web_server.py",
    "jarvis.py":         ROOT / "jarvis.py",
    "index.html":        ROOT / "web/index.html",
    "tools/__init__.py": ROOT / "tools/__init__.py",
}


def _call_openai(content: str, instruction: str, api_key: str) -> str:
    import httpx
    resp = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o-mini",
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a text editor. Apply the instruction to the given content "
                        "and return ONLY the modified content — no markdown fences, "
                        "no explanation, no commentary. Raw content only."
                    ),
                },
                {"role": "user", "content": f"INSTRUCTION: {instruction}\n\nCONTENT:\n{content}"},
            ],
        },
        timeout=120,
    )
    resp.raise_for_status()
    result = resp.json()["choices"][0]["message"]["content"]
    # Strip accidental markdown fences
    if result.startswith("```"):
        lines = result.splitlines()
        result = "\n".join(lines[1:-1] if lines[-1].strip().startswith("```") else lines[1:])
    return result


def _edit_backend(original: str, instruction: str, api_key: str) -> str:
    """For backend.py: edit ONLY the SYSTEM_PROMPT string, never the Python code."""
    m = re.search(r'(SYSTEM_PROMPT\s*=\s*"""\\\n)(.*?)(""")', original, re.DOTALL)
    if not m:
        raise ValueError("Could not locate SYSTEM_PROMPT in backend.py")
    before  = original[:m.start()]
    opener  = m.group(1)
    prompt  = m.group(2)
    closer  = m.group(3)
    after   = original[m.end():]
    new_prompt = _call_openai(prompt, instruction, api_key)
    return before + opener + new_prompt + closer + after


def self_modify_tool():
    def apply_change(file: str, instruction: str):
        try:
            api_key = os.getenv("OPENAI_API_KEY", "")
            if not api_key:
                return {"error": "OPENAI_API_KEY not set", "success": False}

            path = EDITABLE.get(file)
            if path is None:
                candidate = ROOT / file
                if candidate.exists():
                    path = candidate
                else:
                    return {
                        "error": f"Unknown file: {file}. Known: {list(EDITABLE.keys())}",
                        "success": False,
                    }

            original = path.read_text(encoding="utf-8")

            if file == "backend.py":
                # Safe: only rewrites SYSTEM_PROMPT, never touches Python code
                modified = _edit_backend(original, instruction, api_key)
            else:
                # For other files, rewrite in full
                modified = _call_openai(original, instruction, api_key)

            path.write_text(modified, encoding="utf-8")
            return {
                "success": True,
                "file": str(path),
                "instruction": instruction,
                "note": "Saved. Server auto-reloads within seconds.",
            }
        except Exception as e:
            return {"error": str(e), "success": False}

    return create_tool(
        id="apply_code_change",
        description=(
            "Edit one of JARVIS's own source files. "
            "Use this whenever the user asks to change JARVIS's personality, behaviour, rules, or code. "
            "Provide the filename and a plain-English instruction describing what to change. "
            "The server auto-reloads after the edit — no restart needed. "
            "Available files: backend.py (personality, system prompt, model settings), "
            "index.html (web interface), web_server.py (server logic), "
            "tools/__init__.py (tool registry)."
        ),
        execute=apply_change,
        input_schema={
            "type": "object",
            "properties": {
                "file": {
                    "type": "string",
                    "description": "File to edit: backend.py | index.html | web_server.py | tools/__init__.py",
                },
                "instruction": {
                    "type": "string",
                    "description": "Plain-English description of exactly what to change in the file.",
                },
            },
            "required": ["file", "instruction"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "file":    {"type": "string"},
                "note":    {"type": "string"},
                "error":   {"type": "string"},
            },
            "required": [],
        },
    )
