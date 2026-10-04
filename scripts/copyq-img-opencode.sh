#!/bin/bash
# Recibe la imagen seleccionada en CopyQ por stdin, la guarda y escribe la
# ruta en la ventana enfocada (mismo efecto que arrastrar y soltar).
f="/tmp/opencode-img-$(date +%Y%m%d-%H%M%S).png"
cat > "$f"
# Esperar a que CopyQ se oculte y devuelva el foco al terminal
sleep 0.35
xdotool type --delay 25 --clearmodifiers "$f"
