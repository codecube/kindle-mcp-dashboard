#!/bin/sh
# Optional jailbroken-EY21 client. Set DASHBOARD_URL to the server's LAN address.
DASHBOARD_URL="${DASHBOARD_URL:-http://192.168.1.10:8787/screen.png}"
REFRESH_SECONDS="${REFRESH_SECONDS:-60}"
IMAGE=/tmp/kindle-dashboard.png

lipc-set-prop com.lab126.powerd preventScreenSaver 1 2>/dev/null || true
while true; do
    if wget -q -O "$IMAGE.new" "$DASHBOARD_URL"; then
        mv "$IMAGE.new" "$IMAGE"
        if eips -d l=0,w=758,h=1024 -x 0 -y 0 -w gc16; then
            sleep 1
        else
            eips -c
        fi
        eips -f -g "$IMAGE"
    fi
    sleep "$REFRESH_SECONDS"
done
