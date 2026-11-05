#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
APP_DATA="$DATA_HOME/pokedex-player"
APP_DIR="$DATA_HOME/applications"
ICON_DIR="$DATA_HOME/icons/hicolor/scalable/apps"
BIN_DIR="${HOME}/.local/bin"

mkdir -p "$APP_DATA/extension" "$APP_DIR" "$ICON_DIR" "$BIN_DIR"
cp -a "$SOURCE_DIR/extension/." "$APP_DATA/extension/"
install -m 755 "$SOURCE_DIR/launch.sh" "$BIN_DIR/gardevoir-sounddex"
install -m 644 "$SOURCE_DIR/gardevoir-sounddex.svg" "$ICON_DIR/gardevoir-sounddex.svg"

BRAVE_BIN="$(command -v brave || command -v brave-browser || true)"
if [[ -z "$BRAVE_BIN" ]]; then
    echo "No encuentro Brave Browser; el lanzador quedará instalado pero no podrá abrirse todavía." >&2
    BRAVE_BIN="brave"
fi

python - "$SOURCE_DIR/gardevoir-sounddex.desktop.in" "$APP_DIR/gardevoir-sounddex.desktop" "$BIN_DIR/gardevoir-sounddex" "$BRAVE_BIN" "$ICON_DIR/gardevoir-sounddex.svg" <<'PY'
from pathlib import Path
import sys

template, destination, launcher, brave, icon = map(Path, sys.argv[1:])
content = template.read_text()
content = content.replace("@LAUNCHER@", str(launcher))
content = content.replace("@BRAVE@", str(brave))
content = content.replace("@ICON@", str(icon))
destination.write_text(content)
destination.chmod(0o644)
PY

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APP_DIR" 2>/dev/null || true
fi

echo "Gardevoir SoundDex instalado. Búscalo como ‘reproductor’ con Win + Espacio."
echo "La primera vez abre un perfil Brave dedicado; inicia sesión en YouTube Music si la playlist lo requiere."
