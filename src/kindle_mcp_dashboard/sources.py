from __future__ import annotations

import datetime as dt
import platform
from pathlib import Path
from typing import Any

import psutil


def snapshot() -> dict[str, Any]:
    now = dt.datetime.now().astimezone()
    return {
        "system.time": now.strftime("%H:%M"),
        "system.date": now.strftime("%A\n%d %B %Y"),
        "system.hostname": platform.node(),
        "system.cpu_percent": round(psutil.cpu_percent(interval=None)),
        "system.memory_percent": round(psutil.virtual_memory().percent),
        "system.disk_percent": round(psutil.disk_usage(Path.home()).percent),
        "system.load": round(psutil.getloadavg()[0], 2),
        "system.uptime": _duration(dt.timedelta(seconds=int(dt.datetime.now().timestamp() - psutil.boot_time()))),
    }


def resolve(region: dict[str, Any], values: dict[str, Any]) -> Any:
    source = region.get("source")
    return values.get(source, region.get("value", "")) if source else region.get("value", "")


def _duration(value: dt.timedelta) -> str:
    days = value.days
    hours, remainder = divmod(value.seconds, 3600)
    minutes = remainder // 60
    return f"{days}d {hours}h" if days else f"{hours}h {minutes}m"

