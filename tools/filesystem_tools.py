"""File system tools — full read/write/list/delete access."""

import os
import shutil
from pathlib import Path
from fury import create_tool

MAX_READ_BYTES = 5_000_000  # 5 MB — no practical cap

# Common shorthand → real Windows path
_FOLDER_ALIASES = {
    "desktop":   os.path.join(os.path.expanduser("~"), "Desktop"),
    "documents": os.path.join(os.path.expanduser("~"), "Documents"),
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
    "pictures":  os.path.join(os.path.expanduser("~"), "Pictures"),
    "home":      os.path.expanduser("~"),
}

def _resolve(path: str) -> Path:
    """Expand env-vars, ~, and common shorthand names."""
    path = os.path.expandvars(path)          # %USERPROFILE%, $env:... etc.
    lower = path.strip().lower().lstrip("/\\")
    for alias, real in _FOLDER_ALIASES.items():
        if lower.startswith(alias + "/") or lower.startswith(alias + "\\") or lower == alias:
            path = real + path[len(alias):]  # swap alias prefix with real path
            break
    return Path(path).expanduser().resolve()


def list_directory_tool():
    def list_directory(path: str = "."):
        try:
            p = _resolve(path)
            entries = []
            for item in sorted(p.iterdir()):
                entries.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size_bytes": item.stat().st_size if item.is_file() else None,
                })
            return {"path": str(p), "entries": entries, "count": len(entries)}
        except Exception as e:
            return {"error": str(e), "path": path}

    return create_tool(
        id="list_directory",
        description="List files and folders at a given path",
        execute=list_directory,
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (default: current directory)"},
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "path":    {"type": "string"},
                "entries": {"type": "array"},
                "count":   {"type": "integer"},
            },
            "required": [],
        },
    )


def read_file_tool():
    def read_file(path: str, encoding: str = "utf-8"):
        try:
            p = _resolve(path)
            size = p.stat().st_size
            if size > MAX_READ_BYTES:
                content = p.read_bytes()[:MAX_READ_BYTES].decode(encoding, errors="replace")
                return {
                    "path": str(p), "content": content,
                    "truncated": True, "total_bytes": size,
                }
            return {
                "path": str(p),
                "content": p.read_text(encoding=encoding, errors="replace"),
                "truncated": False,
                "total_bytes": size,
            }
        except Exception as e:
            return {"error": str(e), "path": path}

    return create_tool(
        id="read_file",
        description="Read the contents of any text file",
        execute=read_file,
        input_schema={
            "type": "object",
            "properties": {
                "path":     {"type": "string", "description": "Absolute or relative file path"},
                "encoding": {"type": "string", "description": "Text encoding (default utf-8)"},
            },
            "required": ["path"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "path":        {"type": "string"},
                "content":     {"type": "string"},
                "truncated":   {"type": "boolean"},
                "total_bytes": {"type": "integer"},
            },
            "required": [],
        },
    )


def write_file_tool():
    def write_file(path: str, content: str, mode: str = "overwrite"):
        import subprocess, tempfile

        # Strategy 1: direct Python write with smart path resolution
        try:
            p = _resolve(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            flag = "a" if mode == "append" else "w"
            with p.open(flag, encoding="utf-8") as f:
                f.write(content)
            return {"success": True, "path": str(p), "bytes_written": len(content.encode())}
        except Exception as e1:
            pass

        # Strategy 2: PowerShell Set-Content (bypasses any Python path quirks)
        try:
            p = _resolve(path)
            # Write content via a temp file to avoid quoting nightmares
            tmp = tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                              suffix=".tmp", delete=False)
            tmp.write(content)
            tmp.close()
            ps_cmd = (
                f"New-Item -ItemType Directory -Force -Path '{p.parent}' | Out-Null; "
                f"Get-Content -Path '{tmp.name}' -Raw | "
                f"{'Add-Content' if mode == 'append' else 'Set-Content'} -Path '{p}' -Encoding UTF8"
            )
            result = subprocess.run(
                ["powershell", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True, text=True, timeout=30
            )
            os.unlink(tmp.name)
            if result.returncode == 0:
                return {"success": True, "path": str(p), "bytes_written": len(content.encode()),
                        "method": "powershell"}
            return {
                "success": False,
                "error": result.stderr.strip() or result.stdout.strip(),
                "resolved_path": str(p),
            }
        except Exception as e2:
            return {"success": False, "error": str(e2), "resolved_path": str(_resolve(path))}

    return create_tool(
        id="write_file",
        description="Write or append text content to any file (creates parent directories as needed)",
        execute=write_file,
        input_schema={
            "type": "object",
            "properties": {
                "path":    {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Text content to write"},
                "mode":    {"type": "string", "enum": ["overwrite", "append"],
                            "description": "Write mode (default: overwrite)"},
            },
            "required": ["path", "content"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success":       {"type": "boolean"},
                "path":          {"type": "string"},
                "bytes_written": {"type": "integer"},
            },
            "required": [],
        },
    )


def delete_file_tool():
    def delete_file(path: str):
        try:
            p = _resolve(path)
            if p.is_dir():
                shutil.rmtree(p)
                return {"success": True, "path": str(p), "type": "directory"}
            else:
                p.unlink()
                return {"success": True, "path": str(p), "type": "file"}
        except Exception as e:
            return {"error": str(e), "path": path}

    return create_tool(
        id="delete_file",
        description="Delete a file or directory (recursive)",
        execute=delete_file,
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to file or directory to delete"},
            },
            "required": ["path"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "path":    {"type": "string"},
                "type":    {"type": "string"},
            },
            "required": [],
        },
    )


def move_file_tool():
    def move_file(source: str, destination: str):
        try:
            src = _resolve(source)
            dst = _resolve(destination)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            return {"success": True, "source": str(src), "destination": str(dst)}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="move_file",
        description="Move or rename a file or directory",
        execute=move_file,
        input_schema={
            "type": "object",
            "properties": {
                "source":      {"type": "string", "description": "Source path"},
                "destination": {"type": "string", "description": "Destination path"},
            },
            "required": ["source", "destination"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success":     {"type": "boolean"},
                "source":      {"type": "string"},
                "destination": {"type": "string"},
            },
            "required": [],
        },
    )
