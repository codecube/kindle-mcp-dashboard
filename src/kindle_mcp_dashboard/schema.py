from __future__ import annotations

from copy import deepcopy
from typing import Any

KINDS = {"text", "metric", "status", "progress", "list", "image"}


class DashboardError(ValueError):
    pass


def validate_dashboard(value: dict[str, Any]) -> dict[str, Any]:
    data = deepcopy(value)
    device = data.get("device", {})
    for key in ("width", "height"):
        if not isinstance(device.get(key), int) or device[key] <= 0:
            raise DashboardError(f"device.{key} must be a positive integer")
    screens = data.get("screens")
    if not isinstance(screens, list) or not screens:
        raise DashboardError("screens must be a non-empty list")
    screen_ids: set[str] = set()
    for screen in screens:
        sid = _identifier(screen.get("id"), "screen.id")
        if sid in screen_ids:
            raise DashboardError(f"duplicate screen id: {sid}")
        screen_ids.add(sid)
        regions = screen.get("regions")
        if not isinstance(regions, list):
            raise DashboardError(f"screen {sid} regions must be a list")
        region_ids: set[str] = set()
        for region in regions:
            rid = _identifier(region.get("id"), f"screen {sid} region.id")
            if rid in region_ids:
                raise DashboardError(f"duplicate region id in {sid}: {rid}")
            region_ids.add(rid)
            if region.get("kind") not in KINDS:
                raise DashboardError(f"region {rid} has unsupported kind")
            for key in ("x", "y", "w", "h"):
                number = region.get(key)
                if not isinstance(number, (int, float)):
                    raise DashboardError(f"region {rid}.{key} must be numeric")
            if region["w"] <= 0 or region["h"] <= 0:
                raise DashboardError(f"region {rid} must have positive size")
            if region["x"] < 0 or region["y"] < 0 or region["x"] + region["w"] > 1000 or region["y"] + region["h"] > 1000:
                raise DashboardError(f"region {rid} must fit inside the normalized 1000x1000 canvas")
    if data.get("active_screen") not in screen_ids:
        raise DashboardError("active_screen must name an existing screen")
    return data


def _identifier(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or not value.replace("-", "").replace("_", "").isalnum():
        raise DashboardError(f"{field} must contain letters, digits, '_' or '-'")
    return value
