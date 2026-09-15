# Kindle MCP Dashboard

An MCP-controlled, server-rendered e-ink dashboard for the **Amazon Kindle
Paperwhite EY21** (Paperwhite 1, 2012). The renderer targets its 758×1024,
16-level grayscale display and deliberately sends the Kindle a simple PNG.

The Kindle is a display client, not the MCP host:

```text
Claude / Pi / another MCP client
             │ MCP tools
             ▼
   dashboard state + renderer ──── HTTP ────► Kindle EY21
```

This separation keeps API keys and integrations off the old device. MCP clients
can design screens and push weather, hardware, home automation, or agent-control
plane state. Live host time and hardware utilization are resolved when the PNG
is rendered.

## Features

- Named screens with an active-screen switch
- Regions positioned on a normalized 1000×1000 canvas
- `text`, `metric`, `status`, `progress`, and `list` widgets
- Built-in monochrome icons: `weather`/`cloud`, `cpu`, `memory`, `disk`, `agent`
- Atomic JSON persistence shared by the MCP and HTTP processes
- Live sources: `system.time`, `system.date`, `system.hostname`,
  `system.cpu_percent`, `system.memory_percent`, `system.disk_percent`,
  `system.load`, and `system.uptime`
- Browser mode with cache-free periodic refresh
- Optional jailbroken-device `wget` + `eips` refresh script

## Install and run

```bash
cd kindle-mcp-dashboard
python -m venv .venv
.venv/bin/pip install -e .
.venv/bin/kindle-dashboard init
.venv/bin/kindle-dashboard preview
.venv/bin/kindle-dashboard serve --host 0.0.0.0 --port 8787 --refresh 60
```

Port 8787 is the direct dashboard-server port. Find the computer's LAN address
with `ip -br address`. Most clients can open this plain-HTTP URL in the
Experimental Browser:

```text
http://COMPUTER_LAN_IP:8787/kindle
```

For the first-generation EY21 on firmware 5.6.1.1, the Experimental Browser
and the jailbroken device client were tested successfully through standard HTTP
port 80 instead. Configure a reverse proxy from port 80 to the dashboard's
8787 port, then use:

```text
http://COMPUTER_LAN_IP/kindle
```

Store connectivity and Amazon registration are not required. The browser only
needs working local Wi-Fi. If the browser itself cannot open local HTTP pages,
use the optional jailbroken client described below.

## Connect an MCP client

The MCP server uses stdio. Example Claude Code registration:

```bash
claude mcp add kindle-dashboard -- \
  /absolute/path/to/kindle-mcp-dashboard/.venv/bin/kindle-dashboard-mcp
```

Example Codex registration:

```bash
codex mcp add kindle-dashboard -- \
  /absolute/path/to/kindle-mcp-dashboard/.venv/bin/kindle-dashboard-mcp
```

Equivalent generic MCP client configuration:

```json
{
  "mcpServers": {
    "kindle-dashboard": {
      "command": "/absolute/path/to/kindle-mcp-dashboard/.venv/bin/kindle-dashboard-mcp"
    }
  }
}
```

Then ask the agent, for example:

> Update the Kindle overview weather region to show Lisbon, 21 °C, partly cloudy.
> Replace the agent list with Codex running, Claude idle, and CI healthy.

The MCP tools are:

- `get_dashboard`
- `list_screens`
- `activate_screen`
- `upsert_screen`
- `update_region`
- `push_updates`
- `render_preview`

For layout changes, use `upsert_screen`. Coordinates are normalized: `{x: 0,
y: 0, w: 500, h: 500}` is the top-left quarter regardless of device pixels.
Content-only updates should use `update_region` or atomic `push_updates`.

Example update arguments:

```json
{
  "screen_id": "overview",
  "updates": [
    {
      "region_id": "weather",
      "fields": {"value": "21 °C · partly cloudy", "icon": "cloud"}
    },
    {
      "region_id": "agents",
      "fields": {
        "items": [
          {"text": "Codex · running tests", "status": "running"},
          {"text": "Claude · idle", "status": "idle"},
          {"text": "CI · healthy", "status": "healthy"}
        ]
      }
    }
  ]
}
```

## Optional jailbroken EY21 mode

This device is confirmed as firmware **5.6.1.1, build 2689890035**. See the
[firmware-specific deployment notes](docs/EY21-5.6.1.1.md). Its B024 serial
prefix confirms the Wi-Fi Paperwhite 1 variant. The current KindleModding
compatibility data selects WinterBreak2 for this model and firmware, without a
registration or lock-screen-ad prerequisite.

`B024` is a non-unique model-family prefix used only for compatibility lookup;
the dashboard never needs or stores a complete Kindle serial number. Users with
a different device should select or create a matching profile rather than
publishing their full serial.

Once the EY21 is already jailbroken with shell access, copy
`kindle/refresh.sh` to it, make it executable, and change `DASHBOARD_URL` to the
server's LAN address. For this firmware, use the port-80 `/screen.png` URL from
the supplied `dashboard.conf`; the direct `:8787` endpoint was not reliable on
the device. The script disables the screensaver, downloads the current PNG, and
draws it using the Kindle's built-in `eips` command.

The original Paperwhite is also supported by the legacy `kindle` build of
KOReader, which can be useful as a launcher on an already-jailbroken device.

## State and operation

State defaults to:

```text
~/.local/state/kindle-mcp-dashboard/dashboard.json
```

Override it for both processes with `KINDLE_DASHBOARD_STATE`. Run the HTTP
server and MCP server under the same Unix user so they share the same file.

The browser refresh interval defaults to 60 seconds. E-ink panels ghost when
updated too often, so intervals below 30 seconds are discouraged. The HTTP
server enforces a minimum browser refresh of 10 seconds.

The HTTP display server has no authentication. When bound to `0.0.0.0`, its
screen image and `/api/state` are readable by other devices that can reach the
port. Run it only on a trusted LAN or restrict access with a host firewall.

## Development

```bash
.venv/bin/pip install pytest
.venv/bin/pytest
```
