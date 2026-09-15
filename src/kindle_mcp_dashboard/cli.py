from __future__ import annotations

import argparse
import json
from pathlib import Path

from .defaults import DEFAULT_DASHBOARD
from .renderer import render_dashboard
from .sources import snapshot
from .store import DashboardStore
from .web import serve


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP-controlled dashboard for Kindle Paperwhite EY21")
    sub = parser.add_subparsers(dest="command", required=True)
    server = sub.add_parser("serve", help="serve the Kindle display page")
    server.add_argument("--host", default="0.0.0.0")
    server.add_argument("--port", default=8787, type=int)
    server.add_argument("--refresh", default=60, type=int)
    preview = sub.add_parser("preview", help="render a PNG preview")
    preview.add_argument("--output", default="preview.png")
    sub.add_parser("init", help="reset state to the example dashboard")
    sub.add_parser("stats", help="print available live system sources")
    args = parser.parse_args()
    store = DashboardStore()
    if args.command == "serve":
        serve(args.host, args.port, args.refresh)
    elif args.command == "preview":
        path = Path(args.output).resolve()
        render_dashboard(store.read()).save(path, "PNG")
        print(path)
    elif args.command == "init":
        store.write(DEFAULT_DASHBOARD)
        print(store.path)
    elif args.command == "stats":
        print(json.dumps(snapshot(), indent=2))


if __name__ == "__main__":
    main()

