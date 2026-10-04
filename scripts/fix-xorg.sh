#!/bin/bash
cat << 'CONFIG' > /etc/X11/xorg.conf
# NVIDIA Xorg Configuration File
Section "ServerLayout"
    Identifier     "Layout0"
    Screen      0  "Screen0" 0 0
EndSection

Section "Device"
    Identifier     "Device0"
    Driver         "nvidia"
    VendorName     "NVIDIA Corporation"
    BoardName      "GeForce RTX 5060 Ti"
    Option         "TripleBuffer" "True"
EndSection

Section "Screen"
    Identifier     "Screen0"
    Device         "Device0"
    DefaultDepth    24
    Option         "Stereo" "0"
    Option         "nvidiaXineramaInfoOrder" "DFP-1"
    Option         "metamodes" "DP-0: 1920x1080_165 @1920x1080 +0+0 {ViewPortIn=1920x1080, ViewPortOut=1920x1080+0+0}, HDMI-0: 1920x1080_60 @1824x1026 +1920+0 {ViewPortIn=1824x1026, ViewPortOut=1824x1026+48+27}"
    SubSection     "Display"
        Depth       24
    EndSubSection
EndSection
CONFIG
echo "xorg.conf actualizado con sintaxis oficial del driver NVIDIA."
