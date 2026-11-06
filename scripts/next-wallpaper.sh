#!/bin/bash
DIR="${HOME}/Imágenes/Gardevoir/Wallpapers"
if [ ! -d "$DIR" ] && [ -d "${HOME}/Pictures/Gardevoir/Wallpapers" ]; then
    DIR="${HOME}/Pictures/Gardevoir/Wallpapers"
fi

# Soporte para modo silencioso (ideal para timers y cambios automáticos)
SILENT=false
for arg in "$@"; do
    case "$arg" in
        --silent|-s)
            SILENT=true
            ;;
    esac
done

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

# Sonido de brillo Shiny en segundo plano (solo si no es silencioso)
if [ "$SILENT" = false ]; then
    pw-play --volume=0.60 "${HOME}/.local/share/sounds/pokemon/shiny_sparkle.wav" 2>/dev/null &
fi

gsettings set org.cinnamon.desktop.background picture-options 'zoom'
gsettings set org.cinnamon.desktop.background picture-uri "$CHOSEN"

# Extraer el color más saturado y adaptar el tema (síncrono para garantizar que termine antes de salir)
RAW_PATH="${CHOSEN#file://}"
python3 "${HOME}/.local/bin/dynamic-theme.py" "$RAW_PATH"

# Reiniciar Conky con la nueva paleta de colores (vía systemd si está activo, o fallback nativo)
if systemctl --user is-active --quiet conky.service 2>/dev/null; then
    systemctl --user restart conky.service
else
    pkill -x conky 2>/dev/null
    sleep 0.2
    nohup conky -c "${HOME}/.config/conky/gardevoir_glass.conf" >/dev/null 2>&1 &
fi

# Si GLava estaba corriendo (o hay música sonando), reiniciarlo limpio con el nuevo tema
if pgrep -x glava >/dev/null 2>&1; then
    killall -9 glava 2>/dev/null
    sleep 0.2
    nohup glava --desktop >/dev/null 2>&1 &
fi

