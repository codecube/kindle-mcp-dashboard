from copy import deepcopy
import json
from pathlib import Path

from kindle_mcp_dashboard.defaults import DEFAULT_DASHBOARD
from kindle_mcp_dashboard.renderer import render_dashboard, render_png
from kindle_mcp_dashboard.schema import DashboardError, validate_dashboard
from kindle_mcp_dashboard.store import DashboardStore


def test_default_dashboard_targets_ey21():
    data = validate_dashboard(DEFAULT_DASHBOARD)
    assert data["device"]["model"].endswith("EY21")
    assert (data["device"]["width"], data["device"]["height"]) == (758, 1024)


def test_render_has_expected_panel_shape():
    image = render_dashboard(DEFAULT_DASHBOARD, {"system.time": "12:34", "system.date": "Tuesday", "system.hostname": "host", "system.cpu_percent": 12, "system.memory_percent": 34, "system.disk_percent": 56})
    assert image.size == (758, 1024)
    assert image.mode == "L"
    assert render_png(DEFAULT_DASHBOARD).startswith(b"\x89PNG")


def test_render_supports_local_image_region(tmp_path):
    asset = tmp_path / "asset.png"
    from PIL import Image
    Image.new("L", (20, 20), 0).save(asset)
    data = deepcopy(DEFAULT_DASHBOARD)
    data["screens"][0]["regions"] = [{
        "id": "logo",
        "kind": "image",
        "x": 100,
        "y": 100,
        "w": 800,
        "h": 800,
        "image": str(asset),
        "trim": True,
    }]
    data = validate_dashboard(data)
    image = render_dashboard(data)
    assert image.getpixel((379, 512)) == 0


def test_store_updates_region_atomically(tmp_path):
    store = DashboardStore(tmp_path / "state.json")
    store.write(DEFAULT_DASHBOARD)
    store.update_region("overview", "weather", {"value": "18 C, clear", "icon": "weather"})
    assert store.active_screen()["regions"][2]["value"] == "18 C, clear"


def test_rejects_out_of_bounds_region():
    data = deepcopy(DEFAULT_DASHBOARD)
    data["screens"][0]["regions"][0]["w"] = 2000
    try:
        validate_dashboard(data)
    except DashboardError:
        return
    raise AssertionError("invalid region was accepted")


def test_accepts_hyphens_and_underscores_in_identifiers():
    data = deepcopy(DEFAULT_DASHBOARD)
    data["screens"][0]["id"] = "operations-overview"
    data["screens"][0]["regions"][0]["id"] = "local_time"
    data["active_screen"] = "operations-overview"
    checked = validate_dashboard(data)
    assert checked["active_screen"] == "operations-overview"
    assert checked["screens"][0]["regions"][0]["id"] == "local_time"


def test_ey21_package_matches_confirmed_firmware():
    root = Path(__file__).parents[1]
    profile = json.loads((root / "kindle/ey21-5.6.1.1/device.json").read_text())
    assert profile["model"] == "EY21"
    assert profile["variant"] == "Wi-Fi"
    assert profile["serial_prefix"] == "B024"
    assert profile["firmware"] == "5.6.1.1"
    assert profile["build"] == "2689890035"
    menu = json.loads((root / "kindle/ey21-5.6.1.1/extensions/kindle-dashboard/menu.json").read_text())
    for item in menu["items"]:
        assert (root / "kindle/ey21-5.6.1.1/extensions/kindle-dashboard" / item["action"]).exists()
