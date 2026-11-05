# ⚠️ REGLAS Y PREFERENCIAS ESTRICTAS DEL USUARIO (PATINI)

Todos los agentes de IA que operen en este sistema DEBEN cumplir obligatoriamente las siguientes directivas:

## 1. 📸 CAPTURA Y RECORTE DE PANTALLA (Win + Shift + S)
* **ESTRICTAMENTE PROHIBIDO USAR, INSTALAR O CONFIGURAR `flameshot`.**
  * Al usuario le resulta lento, invasivo y no le gusta en absoluto.
* **HERRAMIENTA OBLIGATORIA:** Usar exclusivamente el recorte nativo y rápido de `gnome-screenshot -a`.
* **SCRIPT OFICIAL:** `~/.local/bin/cinnamon-area-screenshot.sh`
  * Debe capturar el área seleccionada, inyectar el PNG en CopyQ (`copyq copy image/png`) y en el portapapeles X11 (`xclip`), y reproducir el sonido nativo de obturador.

## 2. ⌨️ TECLADO Y MÉTODO DE ENTRADA
* **ESTRICTAMENTE PROHIBIDO INSTALAR O ACTIVAR `ibus-typing-booster` ni daemons de autocompletado en el teclado.**
  * Causan input lag, lentitud y sensación pesada al escribir.
* Usar siempre la distribución X11 nativa `latam` (Latinoamericana) sin capas de predicción o IBus intermedio.

## 3. 🌐 NAVEGADOR Y SISTEMA (IDIOMA)
* Mantener siempre `--lang=es-419` en `~/.config/brave-flags.conf`.
* El corrector ortográfico de Brave debe incluir español (`es-ES`, `es-419`).

## 4. 🚀 EXPLORACIÓN Y TERMINAL
* El explorador preferido de terminal es **Yazi** (alias `y`).
* Recordar que `q` sale guardando el directorio actual (`cd`), mientras que `Ctrl + C` o `Q` cancelan.

## 5. 🌸 APLICACIONES NATIVAS GARDEVOIR (Calculadora, TimeDex, Widgets GTK 3)
* **DOCUMENTO MAESTRO DE REGLAS:** Consultar obligatoriamente `scripts/GARDEVOIR_APPS_RULES.md` antes de crear o modificar herramientas visuales de este tipo.
* **FORMATO HANDHELD FIJO:** Usar `set_resizable(False)` y tamaños fijos compactos (ej. `370x520` o `390x560`). Solo maximizar dinámicamente si suena una alarma y restaurar el tamaño fijo al detenerla.
* **CRISTAL OBSIDIAN (Cairo):** Ventanas sin bordes de gestor (`set_decorated(False)`), esquinas redondeadas de 16px, fondo 88% de opacidad tintado con el wallpaper actual (`dom_hex`) y borde neón reactivo (`accent_hex`).
* **CABECERA Y MÁRGENES (Bug EventBox):** `Gtk.EventBox` no aplica padding CSS; la caja interna `h_box` DEBE tener `set_margin_start(16)`, `set_margin_end(14)`, `set_margin_top(10)`, `set_margin_bottom(10)` y la flor `🌸` debe tener `set_margin_end(6)`.
* **EMOJIS E ICONOS:** El ÚNICO emoji permitido en todo el sistema es `🌸`. Todos los demás son iconos de Nerd Font (`JetBrainsMono Nerd Font`). NUNCA juntar un icono Nerd Font con texto en una misma etiqueta `Gtk.Label` con tipografía proporcional (`Inter`), deben ir en etiquetas separadas con espaciador.
* **INDICADOR DE FOCO NEÓN:** `:focus` y `:hover` deben tener resplandor neón intenso (`box-shadow: 0 0 16px {accent}`) para que el usuario siempre distinga con claridad dónde está parado antes de presionar Enter.
* **100% OFFLINE:** Prohibido depender de APIs web externas para funciones locales (ej. horas mundiales usan `zoneinfo` de Python + `/usr/share/zoneinfo/` local).
* **SONIDOS POKÉMON:** Clics con `pw-play ~/.local/share/sounds/pokemon/pokeball_blip.wav` y alarmas en bucle con `Ultra_Necrozma_Gardevoir_Alarm.mp3`.

