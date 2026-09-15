from __future__ import annotations

import json
import os
import tempfile
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from .defaults import DEFAULT_DASHBOARD
from .schema import DashboardError, validate_dashboard


def default_state_path() -> Path:
    configured = os.environ.get("KINDLE_DASHBOARD_STATE")
    return Path(configured).expanduser() if configured else Path.home() / ".local/state/kindle-mcp-dashboard/dashboard.json"


class DashboardStore:
    def __init__(self, path: Path | None = None):
        self.path = path or default_state_path()
        self._lock = threading.RLock()

    def ensure(self) -> None:
        with self._lock:
            if not self.path.exists():
                self.write(DEFAULT_DASHBOARD)

    def read(self) -> dict[str, Any]:
        self.ensure()
        with self._lock:
            return validate_dashboard(json.loads(self.path.read_text(encoding="utf-8")))

    def write(self, data: dict[str, Any]) -> dict[str, Any]:
        checked = validate_dashboard(data)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            fd, name = tempfile.mkstemp(prefix="dashboard-", suffix=".json", dir=self.path.parent)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    json.dump(checked, handle, indent=2, ensure_ascii=False)
                    handle.write("\n")
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(name, self.path)
            finally:
                if os.path.exists(name):
                    os.unlink(name)
        return deepcopy(checked)

    def update(self, mutation: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
        with self._lock:
            data = self.read()
            mutation(data)
            return self.write(data)

    def active_screen(self, data: dict[str, Any] | None = None) -> dict[str, Any]:
        state = data or self.read()
        return next(screen for screen in state["screens"] if screen["id"] == state["active_screen"])

    def activate(self, screen_id: str) -> dict[str, Any]:
        def mutation(data: dict[str, Any]) -> None:
            if screen_id not in {item["id"] for item in data["screens"]}:
                raise DashboardError(f"unknown screen: {screen_id}")
            data["active_screen"] = screen_id
        return self.update(mutation)

    def upsert_screen(self, screen: dict[str, Any]) -> dict[str, Any]:
        def mutation(data: dict[str, Any]) -> None:
            for index, current in enumerate(data["screens"]):
                if current["id"] == screen.get("id"):
                    data["screens"][index] = deepcopy(screen)
                    break
            else:
                data["screens"].append(deepcopy(screen))
        return self.update(mutation)

    def update_region(self, screen_id: str, region_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        protected = {"id", "x", "y", "w", "h", "kind"}
        if protected.intersection(fields):
            raise DashboardError(f"use upsert_screen to change structural fields: {sorted(protected.intersection(fields))}")
        def mutation(data: dict[str, Any]) -> None:
            for screen in data["screens"]:
                if screen["id"] != screen_id:
                    continue
                for region in screen["regions"]:
                    if region["id"] == region_id:
                        region.update(deepcopy(fields))
                        return
                raise DashboardError(f"unknown region: {screen_id}/{region_id}")
            raise DashboardError(f"unknown screen: {screen_id}")
        return self.update(mutation)

