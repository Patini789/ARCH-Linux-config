#!/usr/bin/env bash
set -euo pipefail

PLAYLIST_URL="https://music.youtube.com/playlist?list=PLC-WArzdx0KNF2s1dtTDTFS_SBU64vwt6"
APP_DATA="${XDG_DATA_HOME:-$HOME/.local/share}/pokedex-player"
PROFILE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/gardevoir-sounddex/brave-profile"

if command -v brave >/dev/null 2>&1; then
    BRAVE_BIN="$(command -v brave)"
elif command -v brave-browser >/dev/null 2>&1; then
    BRAVE_BIN="$(command -v brave-browser)"
else
    notify-send "Gardevoir SoundDex" "No encuentro Brave Browser." 2>/dev/null || true
    exit 1
fi

if [[ ! -f "$APP_DATA/extension/manifest.json" ]]; then
    notify-send "Gardevoir SoundDex" "Falta instalar la extensión local. Ejecuta extras/pokedex-player/install.sh." 2>/dev/null || true
    exit 1
fi

exec "$BRAVE_BIN" \
    --user-data-dir="$PROFILE_DIR" \
    --no-first-run \
    --no-default-browser-check \
    --lang=es-419 \
    --autoplay-policy=no-user-gesture-required \
    --load-extension="$APP_DATA/extension" \
    --app="$PLAYLIST_URL" \
    --window-size=1020,700 \
    --class=GardevoirSoundDex \
    --name=GardevoirSoundDex
