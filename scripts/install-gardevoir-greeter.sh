#!/bin/bash
set -e

echo "=== 1. Instalando motor LightDM WebKit2 ==="
pacman -S --noconfirm lightdm-webkit2-greeter

echo "=== 2. Instalando tema Gardevoir Shiny en el sistema ==="
REAL_USER="${SUDO_USER:-$USER}"
USER_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
mkdir -p /usr/share/lightdm-webkit/themes/gardevoir-shiny
if [ -d "$USER_HOME/.local/share/gardevoir-greeter" ]; then
    cp -r "$USER_HOME/.local/share/gardevoir-greeter/"* /usr/share/lightdm-webkit/themes/gardevoir-shiny/
    chmod -R 755 /usr/share/lightdm-webkit/themes/gardevoir-shiny
fi

echo "=== 3. Configurando LightDM para usar WebKit2 ==="
sed -i 's/^#\?greeter-session=.*/greeter-session=lightdm-webkit2-greeter/' /etc/lightdm/lightdm.conf

echo "=== 4. Seleccionando el tema gardevoir-shiny en WebKit2 ==="
mkdir -p /etc/lightdm
cat << 'CONFIG' > /etc/lightdm/lightdm-webkit2-greeter.conf
# LightDM WebKit2 Greeter Configuration
[greeter]
webkit_theme = gardevoir-shiny
allow_keyboard = true
show_keyboard = false
secure_mode = false
screensaver_timeout = 300
CONFIG

echo "=========================================================="
echo "✨ Tema Gardevoir Shiny WebKit2 instalado y activado con éxito!"
echo "=========================================================="
