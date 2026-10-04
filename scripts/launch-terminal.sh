#!/bin/bash
# Abre Kitty: reutiliza instancia existente (instantáneo) o lanza nueva
SOCKET="/tmp/kitty-patini.sock"

if [ -S "$SOCKET" ]; then
    kitty @ --to="unix:$SOCKET" launch --type=os-window 2>/dev/null && exit 0
fi

exec /usr/bin/kitty
