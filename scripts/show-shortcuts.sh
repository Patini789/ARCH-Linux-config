#!/bin/bash

# ==============================================================================
# PANEL DE ATAJOS Y COMANDOS DE TERMINAL (GARDEVOIR / ARCH LINUX)
# ==============================================================================
THEME_CSS="${HOME}/.themes/Gardevoir-Dynamic/cinnamon/cinnamon.css"
ACCENT=""
if [ -f "$THEME_CSS" ]; then
    ACCENT=$(grep -oE 'selection-background-color: #[0-9a-fA-F]{6}' "$THEME_CSS" \
             | grep -oE '#[0-9a-fA-F]{6}' | head -n 1)
fi
if [ -z "$ACCENT" ] && [ -f "${HOME}/.config/conky/gardevoir_glass.conf" ]; then
    ACCENT=$(grep -oE "color1 = '#[0-9a-fA-F]{6}'" "${HOME}/.config/conky/gardevoir_glass.conf" \
             | grep -oE '#[0-9a-fA-F]{6}')
fi
[ -z "$ACCENT" ] && ACCENT="#3584e4"

# ── Color de fondo dominante (del wallpaper) ──────────────────────────────────
BG_HEX=""
WALLPAPER=$(gsettings get org.cinnamon.desktop.background picture-uri 2>/dev/null \
            | tr -d "'" | sed 's|file://||')
if [ -f "$WALLPAPER" ]; then
    BG_HEX=$(python3 - "$WALLPAPER" << 'PYEOF'
import sys, colorsys
from PIL import Image
try:
    im = Image.open(sys.argv[1]).convert("RGB")
    w, h = im.size
    crop = im.crop((0, int(h*0.4), w, h)).resize((60, 60))
    q = crop.quantize(colors=8)
    pal = q.getpalette()[:24]
    counts = sorted(q.getcolors(), reverse=True)
    idx = counts[0][1]
    r, g, b = pal[idx*3:idx*3+3]
    hh, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)
    v2 = min(0.14, v * 0.30)
    s2 = min(0.60, s * 1.15)
    rf, gf, bf = colorsys.hsv_to_rgb(hh, s2, v2)
    print(f"#{int(rf*255):02x}{int(gf*255):02x}{int(bf*255):02x}")
except:
    print("")
PYEOF
)
fi

# ── Accent-dim ────────────────────────────────────────────────────────────────
ACCENT_DIM=$(python3 - "$ACCENT" << 'PYEOF'
import sys, colorsys
h = sys.argv[1].lstrip('#')
r, g, b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
hh, s, v = colorsys.rgb_to_hsv(r, g, b)
rf, gf, bf = colorsys.hsv_to_rgb(hh, s * 0.8, v * 0.45)
print(f"#{int(rf*255):02x}{int(gf*255):02x}{int(bf*255):02x}")
PYEOF
)

# ── Inyectar colores en cheatsheet.rasi ──────────────────────────────────────
RASI="${HOME}/.config/rofi/cheatsheet.rasi"

sed -i "s/accent:      #[0-9a-fA-F]\{6\};/accent:      $ACCENT;/"      "$RASI" 2>/dev/null
sed -i "s/border-color: #[0-9a-fA-F]\{6\};/border-color: $ACCENT;/"   "$RASI" 2>/dev/null
[ -n "$ACCENT_DIM" ] && \
    sed -i "s/accent-dim:  #[0-9a-fA-F]\{6\};/accent-dim:  $ACCENT_DIM;/" "$RASI" 2>/dev/null

if [ -n "$BG_HEX" ]; then
    sed -i "s/bg:          #[0-9a-fA-F]\{6\};/bg:          $BG_HEX;/"  "$RASI" 2>/dev/null

    BG_MID=$(python3 - "$BG_HEX" 0.04 << 'PYEOF'
import sys, colorsys
h = sys.argv[1].lstrip('#'); f = float(sys.argv[2])
r, g, b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
hh, s, v = colorsys.rgb_to_hsv(r, g, b)
rf, gf, bf = colorsys.hsv_to_rgb(hh, s, min(1.0, v + f))
print(f"#{int(rf*255):02x}{int(gf*255):02x}{int(bf*255):02x}")
PYEOF
)
    BG_ALT=$(python3 - "$BG_HEX" 0.08 << 'PYEOF'
import sys, colorsys
h = sys.argv[1].lstrip('#'); f = float(sys.argv[2])
r, g, b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
hh, s, v = colorsys.rgb_to_hsv(r, g, b)
rf, gf, bf = colorsys.hsv_to_rgb(hh, s, min(1.0, v + f))
print(f"#{int(rf*255):02x}{int(gf*255):02x}{int(bf*255):02x}")
PYEOF
)
    BG_SEL=$(python3 - "$BG_HEX" << 'PYEOF'
import sys, colorsys
h = sys.argv[1].lstrip('#')
r, g, b = int(h[0:2],16)/255, int(h[2:4],16)/255, int(h[4:6],16)/255
hh, s, v = colorsys.rgb_to_hsv(r, g, b)
rf, gf, bf = colorsys.hsv_to_rgb(hh, s * 0.7, min(1.0, v + 0.13))
print(f"#{int(rf*255):02x}{int(gf*255):02x}{int(bf*255):02x}")
PYEOF
)
    [ -n "$BG_MID" ] && sed -i "s/bg-mid:      #[0-9a-fA-F]\{6\};/bg-mid:      $BG_MID;/" "$RASI" 2>/dev/null
    [ -n "$BG_ALT" ] && sed -i "s/bg-alt:      #[0-9a-fA-F]\{6\};/bg-alt:      $BG_ALT;/" "$RASI" 2>/dev/null
    [ -n "$BG_SEL" ] && sed -i "s/bg-selected: #[0-9a-fA-F]\{6\};/bg-selected: $BG_SEL;/" "$RASI" 2>/dev/null
fi

# ── Generar lista: SOLO los titulos llevan icono de Pokeball destacado ────────
generate_items() {
    python3 - << 'PYEOF'
import os, sys

icon_dirs = [
    os.path.expanduser("~/.local/share/icons/pokeballs"),
    os.path.expanduser("~/.local/share/gardevoir-greeter"),
]

def with_icon(text, icon_name):
    for d in icon_dirs:
        for candidate in (icon_name, f"icon-{icon_name}"):
            p = os.path.join(d, candidate)
            if os.path.exists(p):
                return f"{text}\0icon\x1f{p}"
    return text

entries = [
    # Titulo 1 con Pokeball
    with_icon("── SISTEMA & VENTANAS ───────────────────────────────────────────────", "pokeball.png"),
    "  [ Win + Espacio ]         ->  Buscador de aplicaciones (Rofi)",
    "  [ Win + Tab ]             ->  Buscar ventanas abiertas en cualquier monitor",
    "  [ Win + X ]               ->  Menu apagar / reiniciar / bloquear / suspender",
    "  [ Win + Enter ]           ->  Abrir terminal Kitty",
    "  [ Win + B ]               ->  Navegador web (Brave)",
    "  [ Win + E ]               ->  Explorador de archivos (Nemo)",
    "  [ Win + G ]               ->  Siguiente fondo 4K + sincronizar RGB",
    "  [ Win + L ]               ->  Bloquear pantalla",
    "  [ Win + Shift + S ]       ->  Captura de region al portapapeles",
    "  [ Win + Shift + C ]       ->  Gardevoir Poké-Calc (Calculadora glass)",
    "  [ Win + Shift + T ]       ->  Gardevoir TimeDex (Reloj / Timer / Alarmas)",
    "  [ Win + V ]               ->  Historial del portapapeles (CopyQ)",
    "  [ Win + W ]               ->  Vista mosaico de ventanas (Overview)",
    "  [ Win + S ]               ->  Vista de escritorios virtuales (Expo)",
    "  [ Win + Shift + <-- --> ] ->  Mover ventana al otro monitor",
    "  [ Win + 1 / 2 / 3 / 4 ]  ->  Cambiar a escritorio virtual",
    "  [ Win + Shift + 1-4 ]     ->  Mover ventana a escritorio virtual",
    "  [ Ctrl + Shift + Esc ]    ->  Monitor del sistema",
    "  [ Win + Q ]               ->  Cerrar ventana activa",
    "  [ Win + F ]               ->  Pantalla completa",
    "  [ Win + D ]               ->  Mostrar / ocultar escritorio",
    "  [ Win + Ctrl + Flechas ]  ->  Dividir ventana (izq / der / arriba)",
    "  [ Win + } / \\ ]           ->  Cambiar idioma de teclado (Español / Inglés)",
    "  [ Win + J ]               ->  Multimedia: Canción anterior",
    "  [ Win + K ]               ->  Multimedia: Play / Pausa",
    "  [ Win + N ]               ->  Multimedia: Siguiente canción",
    "  [ Viewnior ]              ->  Visor rapido de imagenes",
    "  [ Zathura ]               ->  Visor de PDF por teclado",

    # Titulo 2 con Masterball
    with_icon("── TERMINAL -- CLI MODERNO ───────────────────────────────────────────", "masterball.png"),
    "  [ ls / ll / la / tree ]   ->  eza: listar archivos con iconos y colores",
    "  [ cat / bat ]             ->  bat: ver archivos con resaltado de sintaxis",
    "  [ rg / ripgrep ]          ->  ripgrep: busqueda ultra rapida en archivos",
    "  [ fd ]                    ->  fd: buscar archivos y carpetas por nombre",
    "  [ fzf ] Ctrl+R / Ctrl+T   ->  fzf: buscador difuso de comandos y rutas",
    "  [ y / yazi ]              ->  yazi: explorador visual de archivos",
    "  [ btop / htop ]           ->  btop: monitor de CPU, RAM, GPU NVIDIA",
    "  [ fastfetch ]             ->  fastfetch: resumen visual del sistema",
    "  [ pokemon-colorscripts ]  ->  sprites en terminal (-n gardevoir / -r)",
    "  [ yay ]                   ->  gestor de paquetes Arch & AUR",
    "  [ yt-dlp ]                ->  descargar video / audio MP3 de internet",
    "  [ waifu2x ]               ->  reescalar imagenes con IA + GPU Vulkan",
    "  [ lms ]                   ->  LM Studio CLI: modelos locales de IA",
    "  [ opencode ]              ->  asistente IA de programacion en terminal",
    "  [ 7z ]                    ->  comprimir y extraer archivos",
    "  [ set-rgb ]               ->  sincronizar iluminacion RGB con el tema",
    "  [ gpu-stats ]             ->  ver uso % y VRAM de la GPU",
    "  [ ros2 / rviz2 ]          ->  ROS 2 Humble: consola de robotica y visor 3D",

    # Titulo 3 con Superball
    with_icon("── GIT -- CONTROL DE VERSIONES ──────────────────────────────────────", "superball.png"),
    "  [ git status ]            ->  ver estado de archivos y cambios pendientes",
    "  [ git add . ]             ->  preparar todos los cambios para commit",
    "  [ git add <archivo> ]     ->  preparar un archivo especifico",
    "  [ git commit -m ]         ->  guardar cambios con mensaje descriptivo",
    "  [ git commit -am ]        ->  add + commit directo (archivos rastreados)",
    "  [ git fetch ]             ->  descargar novedades del remoto sin mezclar",
    "  [ git pull ]              ->  descargar y fusionar cambios del remoto",
    "  [ git push ]              ->  subir commits al repositorio remoto",
    "  [ git switch -c <rama> ]  ->  crear nueva rama y cambiar a ella",
    "  [ git switch <rama> ]     ->  cambiar a una rama existente",
    "  [ git branch -a ]         ->  listar ramas locales y remotas",
    "  [ git merge <rama> ]      ->  fusionar rama seleccionada en la actual",
    "  [ git log --oneline ]     ->  historial compacto (q para salir)",
    "  [ git diff ]              ->  ver diferencias antes de add (q para salir)",
    "  [ git restore <archivo> ] ->  descartar cambios no guardados en archivo",
    "  [ git restore --staged ]  ->  quitar archivo del area de preparacion",
    "  [ git stash / pop ]       ->  guardar temporalmente cambios / recuperar",
]

sys.stdout.buffer.write(("\n".join(entries) + "\n").encode("utf-8"))
PYEOF
}

# ── Lanzar panel ─────────────────────────────────────────────────────────────
CHOICE=$(generate_items | rofi -dmenu -show-icons -i \
    -theme "${HOME}/.config/rofi/cheatsheet.rasi" \
    -p " ATAJOS")

[[ -z "$CHOICE" || "$CHOICE" == *"SISTEMA"* || "$CHOICE" == *"TERMINAL"* || "$CHOICE" == *"GIT"* ]] && exit 0

case "$CHOICE" in
    *"eza"*|*"ls / ll"*)
        echo "eza -lh --icons --group-directories-first" | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Comando copiado" "eza -lh --icons --group-directories-first"
        ;;
    *"cat / bat"*)
        echo "bat " | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Comando copiado" "bat <archivo>"
        ;;
    *"ripgrep"*|*"rg / ripgrep"*)
        echo 'rg ""' | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Comando copiado" 'rg "texto_a_buscar"'
        ;;
    *"fd ]"*|*"fd:"*)
        echo "fd " | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Comando copiado" "fd <nombre_archivo>"
        ;;
    *"fzf"*)
        notify-send -u normal -i utilities-terminal "Atajos fzf" "Ctrl+R: historial  |  Ctrl+T: archivos  |  Alt+C: carpetas"
        ;;
    *"yazi"*)
        kitty -e yazi &
        ;;
    *"btop"*)
        kitty -e btop &
        ;;
    *"fastfetch"*)
        kitty --hold -e fastfetch &
        ;;
    *"pokemon"*)
        kitty --hold -e bash -c "pokemon-colorscripts -n gardevoir; exec bash" &
        ;;
    *"yay"*)
        echo "yay -Syu" | xclip -selection clipboard
        notify-send -u normal -i system-software-install "Comando copiado" "yay -Syu"
        ;;
    *"yt-dlp"*)
        echo "yt-dlp " | xclip -selection clipboard
        notify-send -u normal -i video-x-generic "Comando copiado" 'yt-dlp "URL"'
        ;;
    *"waifu2x"*)
        echo 'waifu2x-ncnn-vulkan -i input.png -o output.png -s 2 -n 3' | xclip -selection clipboard
        notify-send -u normal -i image-x-generic "Comando copiado" "waifu2x-ncnn-vulkan -i input.png -o output.png"
        ;;
    *"lms"*)
        echo "lms ls" | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "LM Studio CLI" "lms ls  |  lms server start"
        ;;
    *"opencode"*)
        kitty -e opencode &
        ;;
    *"7z"*)
        echo "7z x " | xclip -selection clipboard
        notify-send -u normal -i package-x-generic "Comando copiado" "7z x archivo.zip"
        ;;
    *"set-rgb"*)
        "${HOME}/.local/bin/set-rgb.sh" &
        notify-send -u normal -i preferences-desktop-theme "RGB" "Perfil sincronizado con OpenRGB"
        ;;
    *"gpu-stats"*)
        if command -v nvidia-smi >/dev/null 2>&1; then
            kitty --hold -e watch -n 1 nvidia-smi &
        else
            kitty --hold -e watch -n 1 ~/.local/bin/gpu-stats.sh &
        fi
        ;;
    *"ros2"*|*"rviz2"*)
        kitty --title "ROS 2 Humble (Hawksbill)" -e distrobox enter ros2-humble &
        ;;
    *"Rofi"*|*"aplicaciones"*)
        rofi -show drun &
        ;;
    *"ventanas"*)
        rofi -show window -theme "${HOME}/.config/rofi/cheatsheet.rasi" &
        ;;
    *"apagar"*)
        "${HOME}/.local/bin/power-menu.sh" &
        ;;
    *"Kitty"*|*"terminal"*)
        kitty &
        ;;
    *"Brave"*)
        brave &
        ;;
    *"Nemo"*)
        nemo &
        ;;
    *"fondo"*|*"Siguiente"*)
        "${HOME}/.local/bin/next-wallpaper.sh" &
        ;;
    *"Captura"*)
        "${HOME}/.local/bin/cinnamon-area-screenshot.sh" &
        ;;
    *"Monitor"*)
        gnome-system-monitor &
        ;;
    *"Bloquear"*)
        cinnamon-screensaver-command -l &
        ;;
    *"CopyQ"*)
        "${HOME}/.local/bin/copyq-toggle.sh" &
        ;;
    *"Viewnior"*)
        viewnior &
        ;;
    *"Zathura"*)
        zathura &
        ;;
    *"Cambiar idioma"*|*"idioma de teclado"*)
        "${HOME}/.local/bin/toggle-keyboard-layout.sh" &
        ;;
    *"anterior"*)
        "${HOME}/.local/bin/media-control.sh" previous &
        ;;
    *"Play / Pausa"*|*"Pausa"*)
        "${HOME}/.local/bin/media-control.sh" play-pause &
        ;;
    *"Siguiente canción"*|*"Siguiente"*)
        "${HOME}/.local/bin/media-control.sh" next &
        ;;
    *"git status"*)
        echo "git status" | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git status"
        ;;
    *"git add ."*)
        echo "git add ." | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git add ."
        ;;
    *"git add <archivo>"*)
        echo "git add " | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git add <archivo>"
        ;;
    *"git commit -am"*)
        echo 'git commit -am ""' | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" 'git commit -am "mensaje"'
        ;;
    *"git commit -m"*)
        echo 'git commit -m ""' | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" 'git commit -m "mensaje"'
        ;;
    *"git fetch"*)
        echo "git fetch" | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git fetch"
        ;;
    *"git pull"*)
        echo "git pull" | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git pull"
        ;;
    *"git push"*)
        echo "git push" | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git push"
        ;;
    *"git switch -c"*)
        echo "git switch -c " | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git switch -c <nueva-rama>"
        ;;
    *"git switch <rama>"*)
        echo "git switch " | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git switch <rama>"
        ;;
    *"git branch"*)
        echo "git branch -a" | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git branch -a"
        ;;
    *"git merge"*)
        echo "git merge " | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git merge <rama>"
        ;;
    *"git log"*)
        echo "git log --oneline --graph --all" | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git log --oneline --graph --all"
        ;;
    *"git diff"*)
        echo "git diff" | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git diff"
        ;;
    *"git restore <archivo>"*)
        echo "git restore " | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git restore <archivo>"
        ;;
    *"git restore --staged"*)
        echo "git restore --staged " | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git restore --staged <archivo>"
        ;;
    *"git stash"*)
        echo "git stash" | xclip -selection clipboard
        notify-send -u normal -i utilities-terminal "Git Copiado" "git stash  |  git stash pop"
        ;;
esac
