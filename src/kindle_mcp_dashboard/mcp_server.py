from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .renderer import render_dashboard
from .store import DashboardStore

mcp = FastMCP("Kindle EY21 Dashboard")
store = DashboardStore()


@mcp.tool()
def get_dashboard() -> dict[str, Any]:
    """Return the complete dashboard configuration and current content."""
    return store.read()


@mcp.tool()
def list_screens() -> list[dict[str, Any]]:
    """List screens, their names, region IDs, and which screen is active."""
    data = store.read()
    return [
        {"id": screen["id"], "name": screen.get("name", screen["id"]),
         "active": screen["id"] == data["active_screen"],
         "regions": [region["id"] for region in screen["regions"]]}
        for screen in data["screens"]
    ]


@mcp.tool()
def activate_screen(screen_id: str) -> dict[str, Any]:
    """Make a configured screen visible on the Kindle."""
    data = store.activate(screen_id)
    return {"active_screen": data["active_screen"]}


@mcp.tool()
def upsert_screen(screen: dict[str, Any]) -> dict[str, Any]:
    """Create or replace a screen. Region coordinates use a normalized 1000x1000 canvas."""
    data = store.upsert_screen(screen)
    return {"saved": screen.get("id"), "screen_count": len(data["screens"])}


@mcp.tool()
def update_region(screen_id: str, region_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    """Update region content such as value, label, items, status, icon, unit, size or invert."""
    store.update_region(screen_id, region_id, fields)
    return {"updated": f"{screen_id}/{region_id}", "fields": sorted(fields)}


@mcp.tool()
def push_updates(screen_id: str, updates: list[dict[str, Any]]) -> dict[str, Any]:
    """Atomically apply content updates. Each item needs region_id and fields."""
    def mutation(data: dict[str, Any]) -> None:
        screen = next((item for item in data["screens"] if item["id"] == screen_id), None)
        if screen is None:
            raise ValueError(f"unknown screen: {screen_id}")
        regions = {item["id"]: item for item in screen["regions"]}
        for update in updates:
            region_id = update["region_id"]
            if region_id not in regions:
                raise ValueError(f"unknown region: {screen_id}/{region_id}")
            fields = update.get("fields", {})
            forbidden = {"id", "x", "y", "w", "h", "kind"}.intersection(fields)
            if forbidden:
                raise ValueError(f"structural fields require upsert_screen: {sorted(forbidden)}")
            regions[region_id].update(fields)
    store.update(mutation)
    return {"updated": len(updates), "screen_id": screen_id}


@mcp.tool()
def render_preview(output_path: str = "preview.png") -> dict[str, Any]:
    """Render the current screen to a 758x1024 PNG and return its absolute path."""
    path = Path(output_path).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    render_dashboard(store.read()).save(path, format="PNG")
    return {"path": str(path), "bytes": path.stat().st_size}


@mcp.resource("dashboard://state")
def dashboard_resource() -> str:
    """Current dashboard state as JSON."""
    return json.dumps(store.read(), indent=2)


def main() -> None:
    store.ensure()
    mcp.run()


if __name__ == "__main__":
    main()

