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
