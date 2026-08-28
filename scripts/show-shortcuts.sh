#!/bin/bash

SHORTCUTS=$(cat << 'LIST'
🚀  [ Win + Espacio ]        ->  Buscador Spotlight Apps (Rofi)
📑  [ Win + Tab ]            ->  Buscar Ventanas Abiertas en Cualquier Monitor
⚡  [ Win + X ]              ->  Menú de Apagar / Reiniciar / Bloquear
💻  [ Win + Enter ]          ->  Abrir Terminal Kitty (Pokémon)
📂  [ y ] (En Terminal)      ->  Explorador Yazi con Preview 4K de Imágenes
🖼️   [ Viewnior ]             ->  Visor Rápido de Sprites/Imágenes (Godot)
📕  [ Zathura ]              ->  Visor de PDF Instantáneo por Teclado
🌐  [ Win + B ]              ->  Abrir Navegador Web (Brave)
📂  [ Win + E ]              ->  Explorador de Archivos (Nemo)
🖼️   [ Win + G ]              ->  Siguiente Fondo 4K Gardevoir + RGB Sync
🔒  [ Win + L ]              ->  Bloquear Pantalla (Fondo 4K)
📸  [ Win + Shift + S ]      ->  Captura de Región al Portapapeles
📋  [ Win + V ]              ->  Historial de Portapapeles (CopyQ)
🪟  [ Win + W ]              ->  Vista Mosaico de Ventanas (Overview)
🗂️   [ Win + S ]              ->  Vista de Escritorios Virtuales (Expo)
🖥️   [ Win + Shift + ← / → ]  ->  Mover ventana al otro monitor
🔀  [ Win + 1 / 2 / 3 / 4 ]   ->  Cambiar a Escritorio 1 - 4
🚚  [ Win + Shift + 1-4 ]    ->  Mover ventana a Escritorio 1 - 4
📊  [ Ctrl + Shift + Esc ]   ->  Monitor del Sistema (Tareas)
❌  [ Win + Q ]              ->  Cerrar ventana activa
🔲  [ Win + F ]              ->  Alternar Pantalla Completa
🖥️   [ Win + D ]              ->  Mostrar / Ocultar Escritorio
🪟  [ Win + Ctrl + Flechas ] ->  Acomodar / Dividir Ventana (Izq / Der / Arriba)

❓  [ Win + / ] o [ Win + F1] ->  Abrir este panel de atajos
LIST
)

THEME_CSS="${HOME}/.themes/Gardevoir-Dynamic/cinnamon/cinnamon.css"
if [ -f "$THEME_CSS" ]; then
    ACCENT=$(grep -oE '#[0-9a-fA-F]{6}' "$THEME_CSS" | tail -n 1)
    if [ -n "$ACCENT" ]; then
        sed -i "s/accent: #[0-9a-fA-F]\{6\};/accent: $ACCENT;/" "${HOME}/.config/rofi/cheatsheet.rasi"
        sed -i "s/border-color: #[0-9a-fA-F]\{6\};/border-color: $ACCENT;/" "${HOME}/.config/rofi/cheatsheet.rasi"
    fi
fi

CHOICE=$(echo "$SHORTCUTS" | rofi -dmenu -i -theme "${HOME}/.config/rofi/cheatsheet.rasi" -p "⌨️  ATAJOS")

case "$CHOICE" in
    *"Spotlight"*)
        rofi -show drun &
        ;;
    *"Buscar Ventanas"*)
        rofi -show window -theme "${HOME}/.config/rofi/cheatsheet.rasi" &
        ;;
    *"Menú de Apagar"*)
        "${HOME}/.local/bin/power-menu.sh" &
        ;;
    *"Terminal Kitty"*)
        kitty &
        ;;
    *"Yazi"*)
        kitty -e yazi &
        ;;
    *"Viewnior"*)
        viewnior &
        ;;
    *"Zathura"*)
        zathura &
        ;;
    *"Brave"*)
        brave &
        ;;
    *"Nemo"*)
        nemo &
        ;;
    *"Siguiente Fondo"*)
        "${HOME}/.local/bin/next-wallpaper.sh" &
        ;;
    *"Captura"*)
        gnome-screenshot -a -c &
        ;;
    *"Monitor"*)
        gnome-system-monitor &
        ;;
    *"Bloquear"*)
        cinnamon-screensaver-command -l &
        ;;
    *"CopyQ"*)
        copyq toggle &
        ;;
esac
