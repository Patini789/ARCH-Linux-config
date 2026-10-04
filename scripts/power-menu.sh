#!/bin/bash

# Opciones con iconos claros
OPTIONS="⏻   Apagar Sistema\n🔄  Reiniciar Equipo\n🔒  Bloquear Pantalla\n💤  Suspender\n🚪  Cerrar Sesión\n⚡  Recargar Cinnamon"

pw-play --volume=0.5 "${HOME}/.local/share/sounds/pokemon/pokeball_blip.wav" 2>/dev/null &

THEME_CSS="${HOME}/.themes/Gardevoir-Dynamic/cinnamon/cinnamon.css"
if [ -f "$THEME_CSS" ]; then
    ACCENT=$(grep -oE '#[0-9a-fA-F]{6}' "$THEME_CSS" | grep -vE '#11111b|#000000|#333333|#ffffff|#19120b|#242424' | head -n 1)
    if [ -n "$ACCENT" ]; then
        sed -i "s/accent: #[0-9a-fA-F]\{6\};/accent: $ACCENT;/" "${HOME}/.config/rofi/powermenu.rasi" 2>/dev/null || true
        sed -i "s/border-color: #[0-9a-fA-F]\{6\};/border-color: $ACCENT;/" "${HOME}/.config/rofi/powermenu.rasi" 2>/dev/null || true
        sed -i "s/bg-selected: #[0-9a-fA-F]\{6\};/bg-selected: $ACCENT;/" "${HOME}/.config/rofi/powermenu.rasi" 2>/dev/null || true
    fi
fi

CHOICE=$(echo -e "$OPTIONS" | rofi -dmenu -i -theme "${HOME}/.config/rofi/powermenu.rasi" -p "⚡ MENÚ DE ENERGÍA")

case "$CHOICE" in
    *"Apagar"*)
        systemctl poweroff
        ;;
    *"Reiniciar"*)
        systemctl reboot
        ;;
    *"Bloquear"*)
        cinnamon-screensaver-command -l
        ;;
    *"Suspender"*)
        systemctl suspend
        ;;
    *"Cerrar Sesión"*)
        cinnamon-session-quit --logout --no-prompt
        ;;
    *"Recargar Cinnamon"*)
        cinnamon --replace &
        ;;
esac
