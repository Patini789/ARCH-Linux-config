#!/bin/bash
# 1. Fijar resolución de la tarjeta NVIDIA sin panning
nvidia-settings --assign "CurrentMetaMode=DP-0: 1920x1080 +0+0, HDMI-0: 1920x1080 +1920+0 {ViewPortIn=1824x1026, ViewPortOut=1824x1026+48+27, Panning=1824x1026+1920+0}" 2>/dev/null

# 2. Desactivar panning en xrandr
xrandr --output DP-0 --panning 0x0 --output HDMI-0 --panning 0x0 2>/dev/null

# 3. Establecer DP-0 como monitor principal
xrandr --output DP-0 --primary 2>/dev/null
