#!/usr/bin/env bash
# ==============================================================================
# CONTROL MULTIMEDIA SILENCIOSO (SIN NOTIFICACIONES MOLESTAS)
# ==============================================================================

ACTION="${1:-play-pause}"

case "$ACTION" in
    play-pause|toggle)
        playerctl play-pause 2>/dev/null
        ;;
    next)
        playerctl next 2>/dev/null
        ;;
    previous|prev)
        playerctl previous 2>/dev/null
        ;;
    stop)
        playerctl stop 2>/dev/null
        ;;
esac
