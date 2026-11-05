#!/bin/bash
# ==============================================================================
# NOTA IMPORTANTE: PROHIBIDO USAR FLAMESHOT POR PREFERENCIA EXPRESA DEL USUARIO.
# Se utiliza exclusivamente el recorte nativo y rápido de gnome-screenshot.
# ==============================================================================

# Limpiar procesos colgados previos para garantizar apertura instantánea
pkill -9 -f "gnome-screenshot" 2>/dev/null || true

# Micro-pausa mínima para liberar el teclado en X11
sleep 0.1

TMP_IMG="/tmp/cinnamon_screenshot.png"
rm -f "$TMP_IMG"

# Recorte nativo interactivo con cruceta
gnome-screenshot -a -f "$TMP_IMG"

if [ -s "$TMP_IMG" ]; then
    # 1. Guardar en el historial de CopyQ (Win+V) y activar en el portapapeles (Ctrl+V)
    if command -v copyq >/dev/null 2>&1; then
        copyq write image/png - < "$TMP_IMG" 2>/dev/null && copyq select 0 2>/dev/null
    # 2. Respaldo nativo en X11 clipboard si no está CopyQ
    elif command -v xclip >/dev/null 2>&1; then
        xclip -selection clipboard -t image/png -i "$TMP_IMG" 2>/dev/null
    fi

    # 3. Confirmación auditiva (sin notificación emergente)
    pw-play /usr/share/sounds/freedesktop/stereo/screen-capture.oga 2>/dev/null &
fi



