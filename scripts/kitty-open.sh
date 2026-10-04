#!/bin/bash
# kitty-open.sh — Abre Kitty instantáneamente reutilizando la instancia existente
#
# Si ya hay una instancia de Kitty corriendo (con socket), abre una nueva ventana
# en el mismo proceso (sin reinicializar OpenGL/NVIDIA = ~34ms).
# Si no hay instancia, lanza Kitty normalmente (~450ms con GL_THREADED_OPTIMIZATIONS).

SOCKET="/tmp/kitty-patini.sock"

if [ -S "$SOCKET" ]; then
    # Instancia existente: abrir nueva ventana instantáneamente
    kitty @ --to="unix:$SOCKET" launch --type=os-window 2>/dev/null && exit 0
fi

# Fallback: lanzar instancia nueva
exec /usr/bin/kitty "$@"
