import os
import platform
import subprocess
from fury import create_tool


def system_info_tool():
    def system_info():
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            result = {
                "cpu_percent": cpu,
                "ram_used_gb": round(ram.used / 1e9, 2),
                "ram_total_gb": round(ram.total / 1e9, 2),
                "ram_percent": ram.percent,
                "disk_used_gb": round(disk.used / 1e9, 2),
                "disk_total_gb": round(disk.total / 1e9, 2),
                "disk_percent": disk.percent,
                "os": platform.system(),
                "os_version": platform.version(),
            }
            try:
                battery = psutil.sensors_battery()
                if battery:
                    result["battery_percent"] = battery.percent
                    result["battery_charging"] = battery.power_plugged
            except Exception:
                pass
            return result
        except ImportError:
            return {"error": "psutil not installed — run: pip install psutil"}

    return create_tool(
        id="get_system_info",
        description="Get current system performance stats: CPU usage, RAM, disk space, and battery level",
        execute=system_info,
        input_schema={"type": "object", "properties": {}, "required": []},
        output_schema={
            "type": "object",
            "properties": {
                "cpu_percent": {"type": "number"},
                "ram_percent": {"type": "number"},
                "disk_percent": {"type": "number"},
            },
            "required": [],
        },
    )


def open_app_tool():
    def open_app(app_name: str):
        system = platform.system()
        try:
            if system == "Windows":
                os.startfile(app_name)
            elif system == "Darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([app_name])
            return {"success": True, "app": app_name}
        except Exception as e:
            return {"success": False, "app": app_name, "error": str(e)}

    return create_tool(
        id="open_application",
        description="Open an application by name, e.g. 'notepad', 'chrome', 'spotify', 'calculator'",
        execute=open_app,
        input_schema={
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "description": "Application name or executable path"},
            },
            "required": ["app_name"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "app": {"type": "string"},
            },
            "required": ["success", "app"],
        },
    )
