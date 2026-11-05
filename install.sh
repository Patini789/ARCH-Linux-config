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
    kitty rofi conky zathura zathura-pdf-poppler viewnior yazi \
    ffmpegthumbnailer 7zip jq poppler distrobox podman playerctl \
    openrgb python-pillow ttf-dejavu \
    xdotool xorg-xprop xorg-xrandr \
    fastfetch pipewire-pulse gnome-screenshot copyq gnome-system-monitor \
    ttf-jetbrains-mono-nerd ttf-firacode-nerd inter-font \
    noto-fonts-cjk noto-fonts-emoji \
    hunspell hunspell-es_es base-devel libx11 libxtst \
    python-gobject python-cairo \
    starship eza bat fzf touchegg

# Detección de GPU NVIDIA
if lspci 2>/dev/null | grep -iE 'vga|3d|display' | grep -iq nvidia; then
    echo "🎮 GPU NVIDIA detectada, instalando utilidades NVIDIA..."
    sudo pacman -S --needed --noconfirm nvidia-settings nvidia-utils || true
fi

# Detección de GPU AMD
if lspci 2>/dev/null | grep -iE 'vga|3d|display' | grep -iq amd; then
    echo "⚡ GPU AMD Radeon detectada, instalando drivers y utilidades Mesa..."
    sudo pacman -S --needed --noconfirm mesa vulkan-radeon libva-mesa-driver || true
fi

# Paquetes de AUR (requieren paru/yay). Se instalan si el helper existe.
aur_install() {
    if command -v paru >/dev/null 2>&1; then paru -S --needed --noconfirm "$@";
    elif command -v yay >/dev/null 2>&1; then yay -S --needed --noconfirm "$@";
    else echo "  ⚠️  Helper AUR (paru/yay) no encontrado. Instala manualmente: $*"; fi
}

echo "📦 1b. Instalando paquetes de AUR (opcional)..."
aur_install pokemon-colorscripts glava

echo "📁 2. Copiando configuraciones y temas de usuario..."
mkdir -p ~/.config ~/.themes ~/.icons ~/.local/bin ~/.local/share ~/Pictures/Gardevoir/Wallpapers

cp -r "$DOTFILES_DIR/.config/"* ~/.config/
cp -r "$DOTFILES_DIR/.themes/"* ~/.themes/
cp -a "$DOTFILES_DIR/.icons/"* ~/.icons/
cp -r "$DOTFILES_DIR/scripts/"* ~/.local/bin/
chmod +x ~/.local/bin/*
WALLPAPER_DEST="$HOME/Pictures/Gardevoir/Wallpapers"
[ -d "$HOME/Imágenes" ] && WALLPAPER_DEST="$HOME/Imágenes/Gardevoir/Wallpapers"
mkdir -p "$WALLPAPER_DEST"
cp -r "$DOTFILES_DIR/wallpapers/"* "$WALLPAPER_DEST/"
cp -a "$DOTFILES_DIR/.local/share/"* ~/.local/share/

if [ -f "$DOTFILES_DIR/.bashrc" ]; then
    cp "$DOTFILES_DIR/.bashrc" ~/.bashrc
fi

if command -v fc-cache >/dev/null 2>&1; then
    echo "🔤 Actualizando caché de fuentes de usuario..."
    fc-cache -f ~/.local/share/fonts 2>/dev/null || true
fi

if [ -f "$DOTFILES_DIR/scripts/altcode-daemon.c" ]; then
    echo "⚙️  Compilando daemon de Alt-Codes..."
    gcc -O2 "$DOTFILES_DIR/scripts/altcode-daemon.c" -o ~/.local/bin/altcode-daemon -lX11 -lXtst
    chmod +x ~/.local/bin/altcode-daemon
fi

systemctl --user daemon-reload 2>/dev/null || true
systemctl --user enable altcode-daemon.service 2>/dev/null || true
systemctl --user enable auto-transparency.service 2>/dev/null || true
systemctl --user enable audio-idle-inhibit.service 2>/dev/null || true
systemctl --user enable glava-controller.service 2>/dev/null || true
systemctl --user enable conky.service 2>/dev/null || true
systemctl --user enable --now clean-descargas.timer 2>/dev/null || true
systemctl --user enable --now gardevoir-wallpaper.timer 2>/dev/null || true
# Configurar umbrales realistas para Touchégg (evita que espere 35cm en un touchpad de 9.8cm)
sudo mkdir -p /etc/systemd/system/touchegg.service.d
sudo bash -c 'cat << "EOF" > /etc/systemd/system/touchegg.service.d/override.conf
[Service]
ExecStart=
ExecStart=/usr/bin/touchegg --daemon 10 50
EOF'
sudo systemctl daemon-reload 2>/dev/null || true
sudo systemctl enable --now touchegg.service 2>/dev/null || true

echo "🖼️  3. Aplicando configuraciones de sistema (lightdm, display, fondo 4K, cursores, pantalla de bloqueo y login)..."
sudo mkdir -p /etc/lightdm /usr/share/backgrounds/gardevoir /usr/local/bin /usr/share/icons /usr/share/lightdm-webkit/themes/gardevoir-shiny /usr/share/cinnamon-screensaver

# Cursores en sistema
sudo cp -a "$DOTFILES_DIR/.icons/Gardevoir" /usr/share/icons/ 2>/dev/null || true

# Pantalla de Login LightDM (seguro: evita pantalla negra si web-greeter no está instalado)
if command -v web-greeter >/dev/null 2>&1; then
    echo "🌟 web-greeter detectado en el sistema, aplicando configuración WebKit2..."
    sudo cp "$DOTFILES_DIR/etc/lightdm/lightdm.conf" /etc/lightdm/lightdm.conf 2>/dev/null || true
    sudo cp "$DOTFILES_DIR/etc/lightdm/web-greeter.toml" /etc/lightdm/web-greeter.toml 2>/dev/null || true
    if [ -d "$DOTFILES_DIR/.local/share/gardevoir-greeter" ]; then
        sudo mkdir -p /usr/share/web-greeter/themes/gardevoir-shiny /usr/share/lightdm-webkit/themes/gardevoir-shiny
        sudo cp -a "$DOTFILES_DIR/.local/share/gardevoir-greeter/"* /usr/share/web-greeter/themes/gardevoir-shiny/ 2>/dev/null || true
        sudo cp -a "$DOTFILES_DIR/.local/share/gardevoir-greeter/"* /usr/share/lightdm-webkit/themes/gardevoir-shiny/ 2>/dev/null || true
    fi
else
    echo "ℹ️  web-greeter no instalado todavía; manteniendo lightdm-gtk-greeter para garantizar inicio gráfico seguro..."
    sudo cp "$DOTFILES_DIR/etc/lightdm/lightdm-gtk-greeter.conf" /etc/lightdm/lightdm-gtk-greeter.conf 2>/dev/null || true
fi

# Pantalla de Bloqueo Cinnamon (Constelaciones Shiny)
if [ -f "$DOTFILES_DIR/.local/share/gardevoir-lock/monitorView.py" ]; then
    echo "✨ Instalando Constelaciones Shiny en Cinnamon Screensaver..."
    sudo cp -a /usr/share/cinnamon-screensaver/monitorView.py /usr/share/cinnamon-screensaver/monitorView.py.bak-orig 2>/dev/null || true
    sudo install -m644 "$DOTFILES_DIR/.local/share/gardevoir-lock/monitorView.py" /usr/share/cinnamon-screensaver/monitorView.py 2>/dev/null || true
fi

# Displays y Wallpaper
sudo cp "$DOTFILES_DIR/scripts/fix-displays.sh" /usr/local/bin/fix-displays.sh
sudo chmod +x /usr/local/bin/fix-displays.sh
sudo cp "$DOTFILES_DIR/wallpapers/6356688_upscayl_4x_digital-art-4x.png" /usr/share/backgrounds/gardevoir/wallpaper-4k.png

echo "⌨️ 4. Configurando Cinnamon (atajos, paneles, fuentes y tema)..."
xdg-mime default nemo.desktop inode/directory

if [ -f "$DOTFILES_DIR/cinnamon-settings.dconf" ]; then
    echo "⚡ Restaurando configuración completa de Cinnamon vía dconf..."
    sed "s|/home/patini|$HOME|g" "$DOTFILES_DIR/cinnamon-settings.dconf" | dconf load /org/cinnamon/
fi

gsettings set org.cinnamon.desktop.interface cursor-theme "Gardevoir"
gsettings set org.gnome.desktop.interface cursor-theme "Gardevoir"

echo "🤖 5. Inicializando primer fondo dinámico..."
~/.local/bin/next-wallpaper.sh || true

echo "=========================================="
echo "✨ ¡INSTALACIÓN COMPLETADA CON ÉXITO! ✨"
echo "=========================================="
echo ""
echo "ℹ️  TODO INCLUIDO DIRECTAMENTE EN EL REPO:"
echo "   - Pantalla de bloqueo con Constelaciones Shiny"
echo "   - Pantalla de login WebKit2 Gardevoir Shiny"
echo "   - Sonidos y efectos Pokémon integrados"
echo "   - Fuentes pixel-art para Conky y terminal"
echo "   - Atajos completos y terminal con Starship"
echo "   - Recuerda reiniciar para aplicar lightdm y pantallas."

