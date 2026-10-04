#!/bin/bash
mkdir -p /etc/systemd/system.conf.d /etc/systemd/user.conf.d

cat << 'CONFIG' > /etc/systemd/system.conf.d/10-fast-shutdown.conf
[Manager]
DefaultTimeoutStopSec=4s
DefaultTimeoutAbortSec=4s
CONFIG

cat << 'CONFIG' > /etc/systemd/user.conf.d/10-fast-shutdown.conf
[Manager]
DefaultTimeoutStopSec=3s
DefaultTimeoutAbortSec=3s
CONFIG

systemctl daemon-reload
echo "Tiempos de apagado ultrarrápidos (3-4 segundos) configurados con éxito."
