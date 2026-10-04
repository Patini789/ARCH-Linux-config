#!/bin/bash
echo "=== 1. Optimizando configuración de mkinitcpio ==="
cat << 'CONFIG' > /etc/mkinitcpio.conf
MODULES=(nvidia nvidia_modeset nvidia_uvm nvidia_drm)
BINARIES=()
FILES=()
HOOKS=(base udev autodetect microcode modconf block filesystems fsck)
COMPRESSION="zstd"
COMPRESSION_OPTIONS=(-19 -T0)
CONFIG

echo "=== 2. Reconstruyendo initramfs ultraligero ==="
mkinitcpio -P

echo "=== 3. Optimizando parámetros del Kernel y GRUB ==="
sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT=".*"/GRUB_CMDLINE_LINUX_DEFAULT="loglevel=3 quiet nvidia-drm.modeset=1"/' /etc/default/grub
sed -i 's/GRUB_TIMEOUT=.*/GRUB_TIMEOUT=1/' /etc/default/grub
grub-mkconfig -o /boot/grub/grub.cfg

echo "=== 4. Tamaño final del ramdisk en /boot: ==="
ls -lh /boot/initramfs-linux.img
echo "Optimización completada con éxito. El arranque ahora será ultrarrápido."
