#!/bin/bash
mkdir -p /etc/systemd/logind.conf.d

cat << 'CONFIG' > /etc/systemd/logind.conf.d/10-power-button.conf
[Login]
HandlePowerKey=poweroff
HandlePowerKeyLongPress=poweroff
CONFIG

systemctl restart systemd-logind
echo "Botón físico de encendido/apagado configurado correctamente."
