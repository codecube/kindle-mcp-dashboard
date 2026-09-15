#!/bin/sh
EXTENSION_DIR="$(cd "$(dirname "$0")/.." && pwd)"
. "$EXTENSION_DIR/dashboard.conf"

PID_FILE=/tmp/kindle-mcp-dashboard.pid
IMAGE_FILE=/tmp/kindle-mcp-dashboard.png
LOG_FILE=/mnt/us/kindle-dashboard.log

draw_dashboard() {
    wget -q -T 20 -O "$IMAGE_FILE.new" "$DASHBOARD_URL"
    WGET_STATUS=$?
    if [ "$WGET_STATUS" -eq 0 ]; then
        mv "$IMAGE_FILE.new" "$IMAGE_FILE"
        # Drive every pixel to black before the next full-screen image. This
        # explicit black phase prevents remnants of the previous dashboard
        # from surviving an e-ink waveform update.
        if eips -d l=0,w=758,h=1024 -x 0 -y 0 -w gc16; then
            sleep 1
        else
            # Older eips builds may not support rectangle painting.
            eips -c
        fi
        eips -f -g "$IMAGE_FILE"
        return 0
    fi
    rm -f "$IMAGE_FILE.new"
    date
    echo "Dashboard fetch failed: wget exit $WGET_STATUS; URL=$DASHBOARD_URL"
    ifconfig 2>&1 || true
    route -n 2>&1 || true
    eips 2 2 "Dashboard unavailable (wget $WGET_STATUS)"
    return 1
}
