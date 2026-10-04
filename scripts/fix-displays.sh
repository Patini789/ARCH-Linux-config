#!/bin/bash
export DISPLAY="${DISPLAY:-:0}"

apply_displays() {
    # Solo aplicar si existe nvidia-settings y el monitor DP-0 está conectado
    if ! command -v nvidia-settings >/dev/null 2>&1; then
        return 0
    fi
    if command -v xrandr >/dev/null 2>&1; then
        if ! xrandr 2>/dev/null | grep -q "DP-0 connected"; then
            return 0
        fi
    fi
    nvidia-settings -c "$DISPLAY" --assign "CurrentMetaMode=DP-0: 1920x1080_165 +0+0 {ViewPortIn=1920x1080, ViewPortOut=1920x1080+0+0}, HDMI-0: 1920x1080_60 +1920+0 {ViewPortIn=1920x1080, ViewPortOut=1824x1026+48+27}" >/dev/null 2>&1
}

case "$1" in
    --autostart)
        sleep 2
        apply_displays
        ;;
    --daemon)
        sleep 2
        apply_displays
        while true; do
            xprop -root -spy _NET_SUPPORTING_WM_CHECK 2>/dev/null | while read -r _; do
                sleep 0.8
                apply_displays
            done
            sleep 2
        done
        ;;
    *)
        apply_displays
        ;;
esac

