# 🌸 ESPECIFICACIÓN Y REGLAS DE DISEÑO: APLICACIONES NATIVAS GARDEVOIR

Este documento define la arquitectura, diseño visual, experiencia de usuario (UX) y estándares de código obligatorios para replicar y crear nuevas aplicaciones nativas estilo **Gardevoir Gadgets** (como `gardevoir-calculator` y `gardevoir-timedex`) en Arch Linux + Cinnamon.

---

## 1. 📐 Filosofía y Dimensiones de Ventana

* **Estilo Handheld / Gadget**: Las herramientas deben sentirse como dispositivos compactos, robustos y estilizados (estilo Pokédex de alta gama).
* **Dimensiones Fijas (Sin redimensionar en estado normal)**:
  * Calculadora: `370 x 520 px`
  * TimeDex: `390 x 560 px`
  * **Regla estricta**: Usar `self.set_resizable(False)` en el `__init__`. Las ventanas responsivas libres generan espacios vacíos incómodos en este tipo de utilidades.
* **Excepción de Maximización Dinámica**:
  * Si la aplicación tiene un modo de alerta/alarma que requiera captar la atención total del usuario:
    1. Activar redimensionamiento: `self.set_resizable(True)`
    2. Maximizar: `self.maximize()`
    3. Al descartar o detener la alarma: `self.unmaximize()`, restaurar `self.set_resizable(False)` y forzar el tamaño fijo `self.resize(ancho, alto)`.

---

## 2. 🔮 Estética Visual: Obsidian Glassmorphism (GTK 3 + Cairo)

* **Ventana sin bordes de gestor**: `self.set_decorated(False)`, `self.set_app_paintable(True)`.
* **Soporte de Transparencia Real RGBA**:
  ```python
  screen = self.get_screen()
  visual = screen.get_rgba_visual()
  if visual:
      self.set_visual(visual)
  self.connect("draw", self.on_draw)
  ```
* **Renderizado Cairo (`on_draw`)**:
  * Limpiar el canal alfa completamente con `cairo.OPERATOR_SOURCE` y `cr.set_source_rgba(0, 0, 0, 0)`.
  * Dibujar rectángulo con radio de redondeo exacto de **16 px**.
  * Fondo cristal ahumado al **88% de opacidad**, tintado con el color dominante del wallpaper (`dom_hex`):
    ```python
    dr, dg, db = hex_to_rgb(theme["dom_hex"])
    bg_r = max(0.03, (dr / 255.0) * 0.6)
    bg_g = max(0.04, (dg / 255.0) * 0.6)
    bg_b = max(0.08, (db / 255.0) * 0.7)
    cr.set_source_rgba(bg_r, bg_g, bg_b, 0.88)
    cr.fill_preserve()
    ```
  * Borde neón dinámico con `accent_hex` a 1.2px de grosor (o `horn_pink` parpadeante en caso de alarma activa).

---

## 3. 🛡️ Cabecera y Solución al "Bug de Margen Izquierdo" de GTK 3

En GTK 3, los contenedores `Gtk.EventBox` (usados para arrastrar la ventana sin bordes) **no aplican padding CSS** a la caja hija interna (`Gtk.Box`), provocando que los elementos empiecen en la coordenada $X = 0$ (pegados a la curva del borde).

* **Regla Obligatoria para la Cabecera**:
  ```python
  header = Gtk.EventBox()
  header.get_style_context().add_class("calc-header")
  header.connect("button-press-event", self.on_header_drag)

  h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
  # Márgenes explícitos indispensables:
  h_box.set_margin_start(16)
  h_box.set_margin_end(14)
  h_box.set_margin_top(10)
  h_box.set_margin_bottom(10)
  header.add(h_box)

  # Icono de flor con margen derecho propio:
  flower_lbl = Gtk.Label(label="🌸")
  flower_lbl.override_font(Pango.FontDescription("13"))
  flower_lbl.set_margin_end(6)
  h_box.pack_start(flower_lbl, False, False, 0)

  # Título en Inter Bold / ExtraBold:
  title = Gtk.Label(label="GARDEVOIR <NOMBRE_APP>")
  title.get_style_context().add_class("calc-title")
  h_box.pack_start(title, False, False, 0)

  spacer = Gtk.Box()
  h_box.pack_start(spacer, True, True, 0)

  # Sub-caja derecha de controles (con spacing uniforme de 6px):
  btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
  # [Botones de acción / modo / sonido]
  # Botón Minimizar: 󰍵
  # Botón Cerrar: 󰅖
  h_box.pack_start(btn_box, False, False, 0)
  ```

* **Función de arrastre de ventana**:
  ```python
  def on_header_drag(self, widget, event):
      if event.button == 1 and not self.get_window().get_state() & Gdk.WindowState.MAXIMIZED:
          self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
  ```

---

## 4. 🌸 Reglas Estrictas de Emojis e Iconos Nerd Font

1. **Único emoji permitido en todo el sistema**: La flor de cerezo `🌸` (icono insignia de Gardevoir).
2. **Todos los demás iconos deben ser Nerd Fonts**:
   * Timer: `󰔛`
   * Cronómetro: `󰔚`
   * Alarma: `󰀠`
   * Reloj / Hora: `󰥔`
   * Minimizar: `󰍵`
   * Cerrar: `󰅖`
   * Copiar: `󰅍`
   * Play / Iniciar: `󰐊` o `󰐕`
   * Vuelta: `󰑕`
   * Reiniciar: `󰑐`
   * Sonido activo: `󰕾` / silenciado: `󰝟`
   * Tono / Audio: `󰎆`
   * Check / Offline: `󰄬`
3. **Regla de Separación de Glifos**:
   * NUNCA juntar un glifo Nerd Font con texto en una misma etiqueta (`Gtk.Label`) usando una fuente proporcional (`Inter`), porque el glifo no reserva espacio de avance y se monta sobre las letras contiguas.
   * **Solución**: Usar dos etiquetas separadas dentro de una caja con `spacing=6` o `spacing=8` (una etiqueta para el glifo con fuente monoespaciada `JetBrainsMono Nerd Font` y otra para el texto con `Inter`).

---

## 5. 💡 Indicador de Foco y Cursor Neón ("¿Dónde estás parado?")

El usuario debe distinguir con total claridad qué botón o pestaña tiene el foco de teclado (Tabulador, flechas) o el cursor del ratón antes de presionar Enter:

```css
/* Foco y Hover en Botones y Pestañas */
.tab-btn:focus,
.tab-btn:hover,
.action-btn:focus,
.action-btn:hover,
.calc-btn:focus,
.calc-btn:hover {
    background-color: rgba({ar}, {ag}, {ab}, 0.28);
    border-color: {accent};
    border-bottom: 3.5px solid {accent};
    color: #FFFFFF;
    box-shadow: 0 0 16px rgba({ar}, {ag}, {ab}, 0.85), inset 0 0 8px rgba({ar}, {ag}, {ab}, 0.35);
    outline: none;
}

/* Pestaña Activa */
.tab-btn-active {
    background-color: rgba({ar}, {ag}, {ab}, 0.35);
    border: 1px solid {accent};
    border-bottom: 4px solid {accent};
    color: #FFFFFF;
    font-weight: 800;
    text-shadow: 0 0 12px {accent}, 0 0 24px {accent};
    box-shadow: 0 5px 22px rgba({ar}, {ag}, {ab}, 0.95), inset 0 0 14px rgba({ar}, {ag}, {ab}, 0.45);
}
```

---

## 6. 🔊 Sistema de Sonido Pokémon

* **Efectos de sonido cortos**: Usar `pw-play` (PipeWire nativo) de forma asíncrona no bloqueante:
  ```python
  def play_sound(sound_path=SOUND_BLIP, volume=0.4):
      if os.path.exists(sound_path):
          try:
              subprocess.Popen(["pw-play", f"--volume={volume}", sound_path],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
          except Exception:
              pass
  ```
* **Rutas estándar en el sistema**:
  * Blip / Clic: `~/.local/share/sounds/pokemon/pokeball_blip.wav`
  * Éxito / Guardado: `~/.local/share/sounds/pokemon/item_get.wav`
  * Centro Pokémon: `~/.local/share/sounds/pokemon/pokemon_center_heal.wav`
  * Alarma predeterminada: `~/.local/share/sounds/pokemon/Ultra_Necrozma_Gardevoir_Alarm.mp3`
* **Bucles de audio (Alarmas / Timers)**:
  * Usar `mpg123 -q --loop -1 <archivo.mp3>` o `ffplay -nodisp -loop 0 -volume 100 <archivo>` ejecutado en proceso hijo que se finaliza con `.terminate()` al pulsar Detener o presionar `Espacio` / `Escape`.

---

## 7. 🌐 Autonomía y Funcionamiento 100% Offline

* **Prohibido depender de APIs o consultas a Internet** para funciones esenciales.
* **Husos Horarios y Relojes Mundiales**:
  * Utilizar la biblioteca estándar nativa de Python `zoneinfo` (`import zoneinfo`).
  * `zoneinfo` lee directamente la base de datos IANA local del sistema en `/usr/share/zoneinfo/` instalada en Arch Linux.
  * Los cálculos de diferencia horaria, DST (horario de verano) y días relativos (Hoy/Mañana/Ayer) se hacen de forma instantánea sin gastar datos ni tener latencia de red.
* **Excepción para Clima (Open-Meteo)**:
  * El clima requiere datos externos meteorológicos. Se utiliza exclusivamente la API pública, libre y gratuita de **Open-Meteo** (`open-meteo.com`, sin API key).
  * **Regla Estricta de Caché**: Todo dato de clima DEBE pasar por el motor central `gardevoir-weather.py` con caché en disco (`~/.cache/gardevoir-weather/weather.json`) de mínimo **15 minutos (900 segundos)**. Queda estrictamente prohibido hacer llamadas a red en cada segundo o renderizado.
  * **Resiliencia Offline**: Timeout estricto de 2.5s; si no hay conexión a internet o falla la petición, se devuelve de inmediato el último dato en caché o una advertencia limpia (`󰖐 Clima no disponible`) sin congelar la interfaz ni Conky.
  * **Visualización**: En el reloj de escritorio (Conky) solo se muestra el icono antes de la fecha (`󰖕  Lunes, 12 de Octubre`); en TimeDex se muestra detallado (temperatura, sensación, humedad y descripción).

---

## 8. 🎨 Integración con `dynamic-theme.py`

Las aplicaciones deben sincronizarse en tiempo real cuando el wallpaper del sistema cambia:
* Monitorear el archivo `~/.config/<nombre_app>/theme.json` cada 2 segundos con `GLib.timeout_add(2000, self.check_theme_update)`.
* Al detectar un cambio de `mtime`, recargar los colores hexadecimales y aplicar la plantilla CSS dinámica.

---

## 9. 📁 Estructura de Archivos y Persistencia

Para cualquier nueva aplicación Gardevoir, seguir esta organización:
1. **Script principal**: `~/.local/bin/gardevoir-<nombre>.py` y espejo en `~/ARCH-Linux-config/scripts/gardevoir-<nombre>.py`.
2. **Lanzador bash**: `~/.local/bin/gardevoir-<nombre>` (controla singleton con `xdotool` para activar ventana existente si ya está en ejecución).
3. **Configuración del usuario**: `~/.config/gardevoir-<nombre>/`
   * `config.json`: preferencias del usuario (sonido, pestañas por defecto, listas guardadas).
   * `theme.json`: colores actuales generados por `dynamic-theme.py`.
4. **Acceso directo de escritorio**: `~/.local/share/applications/gardevoir-<nombre>.desktop`.
5. **Atajos de teclado Cinnamon**: Registrados en `cinnamon-settings.dconf` para apertura rápida con combinaciones estilo `Super + tecla`.
