#!/bin/sh
. "$(dirname "$0")/common.sh"

if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    exit 0
fi

lipc-set-prop com.lab126.powerd preventScreenSaver 1 2>/dev/null || true
(
    # Let sh_integration close and repaint the library before taking over the
    # framebuffer. Older Paperwhite firmware needs several seconds here.
    sleep 15
    while true; do
        draw_dashboard
        sleep "$REFRESH_SECONDS"
    done
) >>"$LOG_FILE" 2>&1 &
echo "$!" >"$PID_FILE"
