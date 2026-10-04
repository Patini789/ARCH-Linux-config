#!/bin/bash
# Instala las constelaciones Gardevoir Shiny en la pantalla de bloqueo.
# Siempre respalda desde el original pristine, no desde versiones modificadas.
set -e

REAL_USER="${SUDO_USER:-$USER}"
USER_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
SRC="$USER_HOME/.local/share/gardevoir-lock/monitorView.py"
ORIG="$USER_HOME/.local/share/gardevoir-lock/original-monitorView.py"
DST="/usr/share/cinnamon-screensaver/monitorView.py"

if [ ! -f "$SRC" ] || [ ! -f "$ORIG" ]; then
    echo "No se encuentra la fuente o el original pristine." >&2
    exit 1
fi

sudo cp -a "$ORIG" "$DST.bak-$(date +%F-%H%M%S)"
sudo install -m644 "$SRC" "$DST"

echo "Constelaciones instaladas en la pantalla de bloqueo."
echo "Reiniciando el screensaver para que tome los cambios..."
cinnamon-screensaver-command --exit 2>/dev/null || true
echo "Listo. El proximo bloqueo mostrara las constelaciones."