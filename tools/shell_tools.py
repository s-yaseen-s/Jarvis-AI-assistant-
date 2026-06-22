"""Shell + process management tools — full system command execution."""

import subprocess
import platform
from fury import create_tool

MAX_OUTPUT = 100_000  # chars


def run_command_tool():
    def run_command(command: str, timeout: int = 300):
        try:
            if platform.system() == "Windows":
                proc = subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                    capture_output=True, text=True, timeout=timeout,
                    encoding="utf-8", errors="replace",
                )
            else:
                proc = subprocess.run(
                    command, shell=True, capture_output=True,
                    text=True, timeout=timeout,
                )

            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()

            if len(stdout) > MAX_OUTPUT:
                stdout = stdout[:MAX_OUTPUT] + "\n[...truncated]"
            if len(stderr) > MAX_OUTPUT:
                stderr = stderr[:MAX_OUTPUT] + "\n[...truncated]"

            return {
                "exit_code": proc.returncode,
                "stdout":    stdout,
                "stderr":    stderr,
                "success":   proc.returncode == 0,
            }
        except subprocess.TimeoutExpired:
            return {"error": f"Command timed out after {timeout}s", "success": False}
        except Exception as e:
            return {"error": str(e), "success": False}

    return create_tool(
        id="run_command",
        description=(
            "Run any PowerShell (Windows) or shell command and return the output. "
            "Use for system tasks, scripts, installs, automation, and anything the OS can do."
        ),
        execute=run_command,
        input_schema={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The command to execute"},
                "timeout": {"type": "integer",
                            "description": "Max seconds to wait (default 300)"},
            },
            "required": ["command"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "exit_code": {"type": "integer"},
                "stdout":    {"type": "string"},
                "stderr":    {"type": "string"},
                "success":   {"type": "boolean"},
            },
            "required": [],
        },
    )


def list_processes_tool():
    def list_processes(filter_name: str = ""):
        try:
            import psutil
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    info = p.info
                    if filter_name.lower() in (info.get("name") or "").lower():
                        procs.append(info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            procs.sort(key=lambda x: x.get("cpu_percent") or 0, reverse=True)
            return {"processes": procs[:50], "total": len(procs)}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="list_processes",
        description="List running processes, optionally filtered by name",
        execute=list_processes,
        input_schema={
            "type": "object",
            "properties": {
                "filter_name": {"type": "string",
                                "description": "Filter by process name (empty = all)"},
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "processes": {"type": "array"},
                "total":     {"type": "integer"},
            },
            "required": [],
        },
    )


def kill_process_tool():
    def kill_process(name: str = "", pid: int = 0):
        try:
            import psutil
            killed = []
            for p in psutil.process_iter(["pid", "name"]):
                try:
                    if (name and name.lower() in (p.info["name"] or "").lower()) or \
                       (pid and p.info["pid"] == pid):
                        p.kill()
                        killed.append({"pid": p.info["pid"], "name": p.info["name"]})
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return {"killed": killed, "count": len(killed)}
        except Exception as e:
            return {"error": str(e)}

    return create_tool(
        id="kill_process",
        description="Kill a running process by name or PID",
        execute=kill_process,
        input_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Process name to kill (partial match)"},
                "pid":  {"type": "integer", "description": "Process ID to kill"},
            },
            "required": [],
        },
        output_schema={
            "type": "object",
            "properties": {
                "killed": {"type": "array"},
                "count":  {"type": "integer"},
            },
            "required": [],
        },
    )
