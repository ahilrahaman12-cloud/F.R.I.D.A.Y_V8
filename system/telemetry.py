"""Live local system telemetry for the dashboard."""

import os
import socket

import psutil


def get_system_state() -> dict[str, object]:
    """Return a best-effort snapshot without failing the user interface."""
    memory = psutil.virtual_memory()
    state: dict[str, object] = {
        "cpu": round(psutil.cpu_percent(interval=None)),
        "ram": round(memory.percent),
        "tasks": len(psutil.pids()),
        "memory": f"{memory.used / (1024 ** 3):.1f} GB",
        "status": "OPERATIONAL",
    }
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        state["network"] = probe.getsockname()[0]
        probe.close()
    except OSError:
        state["network"] = "Offline"
    try:
        disk = psutil.disk_usage(os.path.expanduser("~"))
        state["disk_used"] = f"{disk.used / (1024 ** 3):.1f} GB"
        state["disk_total"] = f"{disk.total / (1024 ** 3):.1f} GB"
    except OSError:
        pass
    return state
