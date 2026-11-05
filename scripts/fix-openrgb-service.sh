#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "⚠️ Por favor ejecuta este script con sudo: sudo $0"
    exit 1
fi

cat << 'SERVICE' > /etc/systemd/system/openrgb-boot.service
[Unit]
Description=OpenRGB Gardevoir: iluminacion de teclado, raton, RAM y placa desde el login
After=multi-user.target

[Service]
Type=oneshot
ExecStartPre=/bin/sleep 2
ExecStart=/usr/bin/openrgb --device "Logitech G213" --mode Direct --color 00ffff --device "G502" --mode Static --color 00ffff --device "Kingston" --mode Static --color 00ffff --device "ASUS" --mode Static --color 00ffff
RemainAfterExit=true

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable openrgb-boot.service
systemctl restart openrgb-boot.service
echo "✨ Servicio OpenRGB de arranque actualizado y probado con éxito."
