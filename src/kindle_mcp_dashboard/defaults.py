from __future__ import annotations

DEFAULT_DASHBOARD = {
    "version": 1,
    "device": {
        "model": "Amazon Kindle Paperwhite EY21",
        "width": 758,
        "height": 1024,
        "grayscale": 16,
    },
    "active_screen": "overview",
    "screens": [
        {
            "id": "overview",
            "name": "Operations overview",
            "regions": [
                {"id": "clock", "kind": "metric", "x": 25, "y": 20, "w": 475, "h": 135,
                 "label": "LOCAL TIME", "source": "system.time", "size": 64},
                {"id": "date", "kind": "text", "x": 515, "y": 20, "w": 460, "h": 135,
                 "label": "TODAY", "source": "system.date", "size": 26},
                {"id": "weather", "kind": "metric", "x": 25, "y": 175, "w": 950, "h": 220,
                 "label": "WEATHER", "icon": "cloud", "value": "Waiting for weather", "unit": "", "size": 46},
                {"id": "cpu", "kind": "progress", "x": 25, "y": 415, "w": 300, "h": 190,
                 "label": "CPU", "icon": "cpu", "source": "system.cpu_percent"},
                {"id": "memory", "kind": "progress", "x": 350, "y": 415, "w": 300, "h": 190,
                 "label": "MEMORY", "icon": "memory", "source": "system.memory_percent"},
                {"id": "disk", "kind": "progress", "x": 675, "y": 415, "w": 300, "h": 190,
                 "label": "DISK", "icon": "disk", "source": "system.disk_percent"},
                {"id": "agents", "kind": "list", "x": 25, "y": 625, "w": 950, "h": 330,
                 "label": "AGENT CONTROL PLANE",
                 "items": ["No agent status received"]},
                {"id": "footer", "kind": "text", "x": 25, "y": 970, "w": 950, "h": 25,
                 "source": "system.hostname", "align": "right", "border": False, "size": 16},
            ],
        }
    ],
}
