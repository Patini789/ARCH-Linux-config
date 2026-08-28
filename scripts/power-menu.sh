#!/bin/bash

# Opciones con iconos claros
OPTIONS="⏻   Apagar Sistema\n🔄  Reiniciar Equipo\n🔒  Bloquear Pantalla\n💤  Suspender\n🚪  Cerrar Sesión\n⚡  Recargar Entorno (Cinnamon)"

# Sincronizar color de acento si existe
THEME_CSS="${HOME}/.themes/Gardevoir-Dynamic/cinnamon/cinnamon.css"
if [ -f "$THEME_CSS" ]; then
    ACCENT=$(grep -oE '#[0-9a-fA-F]{6}' "$THEME_CSS" | tail -n 1)
    if [ -n "$ACCENT" ]; then
        sed -i "s/accent: #[0-9a-fA-F]\{6\};/accent: $ACCENT;/" "${HOME}/.config/rofi/cheatsheet.rasi"
        sed -i "s/border-color: #[0-9a-fA-F]\{6\};/border-color: $ACCENT;/" "${HOME}/.config/rofi/cheatsheet.rasi"
    fi
fi

CHOICE=$(echo -e "$OPTIONS" | rofi -dmenu -i -theme "${HOME}/.config/rofi/cheatsheet.rasi" -p "⚡ POWER MENU")

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
    *"Recargar Entorno"*)
        cinnamon --replace &
        ;;
esac
