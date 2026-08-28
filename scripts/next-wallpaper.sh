#!/bin/bash
DIR="${HOME}/Pictures/Gardevoir/Wallpapers"

mapfile -t IMAGES < <(find "$DIR" -maxdepth 1 -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \))

if [ ${#IMAGES[@]} -eq 0 ]; then
    exit 1
fi

CURRENT=$(gsettings get org.cinnamon.desktop.background picture-uri | tr -d "'")

CHOSEN="$CURRENT"
while [ "$CHOSEN" == "$CURRENT" ] && [ ${#IMAGES[@]} -gt 1 ]; do
    CHOSEN="file://${IMAGES[$(( RANDOM % ${#IMAGES[@]} ))]}"
done

if [ -z "$CHOSEN" ]; then
    CHOSEN="file://${IMAGES[0]}"
fi

# Reproducir sonido de brillo Shiny en segundo plano
pw-play --volume=0.60 "${HOME}/.local/share/sounds/pokemon/shiny_sparkle.wav" 2>/dev/null &

gsettings set org.cinnamon.desktop.background picture-options 'zoom'
gsettings set org.cinnamon.desktop.background picture-uri "$CHOSEN"

# Extraer el color más saturado y adaptar el tema de la barra y las luces RGB
RAW_PATH="${CHOSEN#file://}"
python3 "${HOME}/.local/bin/dynamic-theme.py" "$RAW_PATH" >/dev/null 2>&1 &
