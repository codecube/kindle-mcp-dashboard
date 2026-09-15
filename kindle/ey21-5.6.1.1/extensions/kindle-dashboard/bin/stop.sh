#!/bin/sh
. "$(dirname "$0")/common.sh"

if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE")"
    kill "$PID" 2>/dev/null || true
    rm -f "$PID_FILE"
fi
lipc-set-prop com.lab126.powerd preventScreenSaver 0 2>/dev/null || true
eips -c
eips 2 2 "MCP Dashboard stopped"

