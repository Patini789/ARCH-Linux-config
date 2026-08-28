#!/bin/bash
set -e

echo "=========================================="
echo "🌸 INSTALADOR AUTOMÁTICO GARDEVOIR SETUP 🌸"
echo "=========================================="

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📦 1. Instalando paquetes esenciales (repos oficiales)..."

# Herramientas de la interfaz y dependencias de los scripts (incluye las que
# antes faltaban y las usadas por los atajos).
sudo pacman -S --needed --noconfirm \
    kitty rofi conky glava zathura zathura-pdf-poppler viewnior yazi \
    ffmpegthumbnailer 7zip jq poppler distrobox podman playerctl \
    openrgb python-pillow ttf-dejavu \
    xdotool xorg-xprop xorg-xrandr nvidia-settings nvidia-utils \
    fastfetch pipewire-pulse gnome-screenshot copyq gnome-system-monitor \
    ttf-jetbrains-mono-nerd ttf-firacode-nerd inter-font

# Paquetes de AUR (requieren paru/yay). Se instalan si el helper existe.
aur_install() {
    if command -v paru >/dev/null 2>&1; then paru -S --needed --noconfirm "$@";
    elif command -v yay >/dev/null 2>&1; then yay -S --needed --noconfirm "$@";
    else echo "  ⚠️  Helper AUR (paru/yay) no encontrado. Instala manualmente: $*"; fi
}

echo "📦 1b. Instalando paquetes de AUR (opcional)..."
aur_install pokemon-colorscripts

echo "📁 2. Copiando configuraciones y temas de usuario..."
mkdir -p ~/.config ~/.themes ~/.local/bin ~/Pictures/Gardevoir/Wallpapers

cp -r "$DOTFILES_DIR/.config/"* ~/.config/
cp -r "$DOTFILES_DIR/.themes/"* ~/.themes/
cp -r "$DOTFILES_DIR/scripts/"* ~/.local/bin/
chmod +x ~/.local/bin/*
cp -r "$DOTFILES_DIR/wallpapers/"* ~/Pictures/Gardevoir/Wallpapers/

echo "🖼️  3. Aplicando configuraciones de sistema (lightdm, display, fondo 4K)..."
sudo mkdir -p /etc/lightdm /usr/share/backgrounds/gardevoir /usr/local/bin
sudo cp "$DOTFILES_DIR/etc/lightdm/lightdm.conf" /etc/lightdm/lightdm.conf
sudo cp "$DOTFILES_DIR/etc/lightdm/web-greeter.toml" /etc/lightdm/web-greeter.toml
sudo cp "$DOTFILES_DIR/etc/lightdm/lightdm-gtk-greeter.conf" /etc/lightdm/lightdm-gtk-greeter.conf
sudo cp "$DOTFILES_DIR/scripts/fix-displays.sh" /usr/local/bin/fix-displays.sh
sudo chmod +x /usr/local/bin/fix-displays.sh
sudo cp "$DOTFILES_DIR/wallpapers/6356688_upscayl_4x_digital-art-4x.png" /usr/share/backgrounds/gardevoir/wallpaper-4k.png

echo "⌨️ 4. Configurando atajos de teclado y tema de Cinnamon..."
gsettings set org.cinnamon.theme name "Gardevoir-Dynamic"

gsettings set org.cinnamon.desktop.keybindings custom-list "['custom0', 'custom1', 'custom2', 'custom3', 'custom4', 'custom5', 'custom6', 'custom7']"

gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom0/ name "Rofi Spotlight"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom0/ command "rofi -show drun"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom0/ binding "['<Super>space']"

gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom1/ name "Terminal Kitty"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom1/ command "kitty"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom1/ binding "['<Super>Return']"

gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom2/ name "Navegador Brave"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom2/ command "brave"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom2/ binding "['<Super>b']"

gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom3/ name "Explorador Nemo"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom3/ command "nemo"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom3/ binding "['<Super>e']"

gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom4/ name "Siguiente Fondo Gardevoir"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom4/ command "$HOME/.local/bin/next-wallpaper.sh"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom4/ binding "['<Super>g']"

gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom5/ name "Panel de Atajos"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom5/ command "$HOME/.local/bin/show-shortcuts.sh"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom5/ binding "['<Super>slash', '<Super>F1']"

gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom6/ name "Buscador de Ventanas"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom6/ command "rofi -show window"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom6/ binding "['<Super>Tab']"

gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom7/ name "Menu de Energia"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom7/ command "$HOME/.local/bin/power-menu.sh"
gsettings set org.cinnamon.desktop.keybindings.custom-keybinding:/org/cinnamon/desktop/keybindings/custom-keybindings/custom7/ binding "['<Super>x']"

echo "🤖 5. Inicializando primer fondo dinámico..."
~/.local/bin/next-wallpaper.sh || true

echo "=========================================="
echo "✨ ¡INSTALACIÓN COMPLETADA CON ÉXITO! ✨"
echo "=========================================="
echo ""
echo "ℹ️  PIEZAS NO INCLUIDAS EN EL REPO (a instalar manualmente):"
echo "   - Theme de web-greeter 'gardevoir-shiny' (en /usr/share/web-greeter/themes)"
echo "   - Sonidos de Pokémon en ~/.local/share/sounds/pokemon/*.ogg | *.wav"
echo "   - Theme de iconos 'Papirus-Dark'"
echo "   - Recuerda reiniciar para aplicar lightdm/display-setup-script."
