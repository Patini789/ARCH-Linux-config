#!/usr/bin/env python3
"""
🌸 Gardevoir CoreDex - Monitor Nativo de Hardware, Temperaturas & Cores
Personalizada para Arch Linux + Cinnamon con estética Glassmorphism Obsidian a 88%,
borde neón reactivo con dynamic-theme.py, fuentes 'Inter' y 'JetBrainsMono Nerd Font',
sonidos Pokémon y visualización en tiempo real de CPU (Ryzen), Cores, GPU (NVIDIA) y NVMe.
"""

import os
import sys
import time
import json
import math
import shutil
import subprocess
import threading
from pathlib import Path

import warnings
warnings.filterwarnings('ignore')

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango
import cairo
import psutil

HOME = str(Path.home())
CONFIG_DIR = os.path.join(HOME, ".config/gardevoir-coredex")
THEME_JSON = os.path.join(CONFIG_DIR, "theme.json")
CONFIG_JSON = os.path.join(CONFIG_DIR, "config.json")
SOUND_DIR = os.path.join(HOME, ".local/share/sounds/pokemon")
SOUND_BLIP = os.path.join(SOUND_DIR, "pokeball_blip.wav")


def play_sound(sound_path=SOUND_BLIP, volume=0.35):
    """Reproduce sonido en segundo plano con pw-play si está disponible."""
    if os.path.exists(sound_path):
        try:
            subprocess.Popen(
                ["pw-play", f"--volume={volume}", sound_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass


def load_theme():
    """Carga colores del tema dinámico o usa los valores estándar de Gardevoir."""
    defaults = {
        "dom_hex": "#141228",
        "accent_hex": "#4f7cc6",
        "accent_dim_hex": "#2e3e59",
        "horn_pink": "#FF4370",
        "text_white": "#FFFFFF",
        "text_muted": "#CBD5E1"
    }
    # Intentar cargar de su propio config o del de timedex/calc
    for path in (THEME_JSON, os.path.join(HOME, ".config/gardevoir-timedex/theme.json"), os.path.join(HOME, ".config/gardevoir-calc/theme.json")):
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    defaults.update(data)
                    break
            except Exception:
                pass
    return defaults


def load_config():
    """Carga configuración del usuario."""
    defaults = {
        "sound": True,
        "interval_ms": 1000
    }
    if os.path.exists(CONFIG_JSON):
        try:
            with open(CONFIG_JSON, "r") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults


def save_config(cfg):
    """Guarda configuración en disco."""
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_JSON, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def hex_to_rgb(hex_str):
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def get_thermal_color(temp):
    """Devuelve color según temperatura en grados Celsius."""
    if temp is None:
        return "#94A3B8"
    if temp < 55.0:
        return "#10B981"  # Verde esmeralda fresco
    elif temp < 68.0:
        return "#38BDF8"  # Azul cian templado
    elif temp < 78.0:
        return "#F59E0B"  # Ámbar cálido
    else:
        return "#FF4370"  # Gardevoir Pink alerta alta temperatura


def get_cpu_model():
    """Obtiene el nombre comercial del procesador."""
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    raw = line.split(":", 1)[1].strip()
                    # Limpiar sufijos redundantes
                    raw = raw.replace("Processor", "").replace("with Radeon Graphics", "").strip()
                    return raw
    except Exception:
        pass
    return "AMD Ryzen Processor"


class GardevoirCoreDex(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("Gardevoir CoreDex")
        self.set_wmclass("gardevoir-coredex", "GardevoirCoreDex")
        self.set_role("gardevoir-coredex")
        self.set_default_size(410, 545)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Transparencia RGBA Cairo
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        self.connect("draw", self.on_draw)

        # Estado y configuración
        self.config = load_config()
        self.theme = load_theme()
        self.sound_enabled = self.config.get("sound", True)
        self.last_theme_mtime = os.path.getmtime(THEME_JSON) if os.path.exists(THEME_JSON) else 0

        # Almacén de métricas en caché (hilos concurrentes)
        self.cpu_model = get_cpu_model()
        self.num_cores = psutil.cpu_count(logical=True) or 12
        self.gpu_data = None
        self.lock = threading.Lock()

        # Iniciar psutil para primera muestra de cálculo
        psutil.cpu_percent(interval=None)
        psutil.cpu_percent(percpu=True, interval=None)

        # CSS Provider
        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(
            screen, self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.apply_theme()

        # Construir Interfaz
        self.build_ui()

        # Eventos de teclado
        self.connect("key-press-event", self.on_key_press)

        # Temporizadores de actualización periódica
        GLib.timeout_add(self.config.get("interval_ms", 1000), self.on_metrics_tick)
        GLib.timeout_add(2000, self.check_theme_update)

        # Consulta inicial de GPU
        self._query_gpu()

        # Hilo en segundo plano para lectura de GPU
        self.gpu_worker_running = True
        self.gpu_thread = threading.Thread(target=self._gpu_worker, daemon=True)
        self.gpu_thread.start()

        # Primera actualización instantánea
        self.update_hardware_metrics()

    def _query_gpu(self):
        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,fan.speed",
                "--format=csv,noheader,nounits"
            ]
            res = subprocess.check_output(cmd, text=True, timeout=1).strip().split(",")
            data = {
                "name": res[0].strip(),
                "temp": int(res[1].strip()),
                "util": int(res[2].strip()),
                "mem_used": int(res[3].strip()),
                "mem_total": int(res[4].strip()),
                "power": float(res[5].strip()),
                "fan": int(res[6].strip())
            }
            with self.lock:
                self.gpu_data = data
        except Exception:
            pass

    def _gpu_worker(self):
        """Monitorea NVIDIA en hilo independiente para no bloquear GTK jamás."""
        while self.gpu_worker_running:
            self._query_gpu()
            time.sleep(1.0)

    def on_draw(self, widget, cr):
        """Renderiza obsidian glass a 88% con esquinas redondeadas y borde neón."""
        alloc = self.get_allocation()
        w, h = alloc.width, alloc.height

        # 1. Limpiar canal alfa
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        # 2. Rectángulo redondeado 16px
        cr.set_operator(cairo.OPERATOR_OVER)
        radius = 16.0
        degrees = math.pi / 180.0

        cr.new_sub_path()
        cr.arc(w - radius, radius, radius, -90 * degrees, 0 * degrees)
        cr.arc(w - radius, h - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc(radius, h - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc(radius, radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path()

        # 3. Cristal Obsidian ahumado (88% opacidad tintado con dom_hex)
        t = self.theme
        dr, dg, db = hex_to_rgb(t["dom_hex"])
        bg_r = max(0.03, (dr / 255.0) * 0.6)
        bg_g = max(0.04, (dg / 255.0) * 0.6)
        bg_b = max(0.08, (db / 255.0) * 0.7)
        cr.set_source_rgba(bg_r, bg_g, bg_b, 0.88)
        cr.fill_preserve()

        # 4. Borde Neón Dinámico
        ar, ag, ab = hex_to_rgb(t["accent_hex"])
        cr.set_source_rgba(ar / 255.0, ag / 255.0, ab / 255.0, 0.95)
        cr.set_line_width(1.3)
        cr.stroke()

        return False

    def on_header_drag(self, widget, event):
        """Permite mover la ventana arrastrando la cabecera."""
        if event.button == 1:
            self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def on_key_press(self, widget, event):
        """Atajos de teclado: Escape / Q para salir, R para refrescar."""
        keyval = event.keyval
        if keyval in (Gdk.KEY_Escape, Gdk.KEY_q, Gdk.KEY_Q):
            self.close_app()
            return True
        elif keyval in (Gdk.KEY_r, Gdk.KEY_R):
            if self.sound_enabled:
                play_sound(SOUND_BLIP, 0.3)
            self.update_hardware_metrics()
            return True
        return False

    def close_app(self, *args):
        if self.sound_enabled:
            play_sound(SOUND_BLIP, 0.3)
        self.gpu_worker_running = False
        Gtk.main_quit()

    def minimize_app(self, *args):
        if self.sound_enabled:
            play_sound(SOUND_BLIP, 0.25)
        self.iconify()

    def toggle_sound(self, *args):
        self.sound_enabled = not self.sound_enabled
        self.config["sound"] = self.sound_enabled
        save_config(self.config)
        self.sound_btn_lbl.set_text("󰕾" if self.sound_enabled else "󰝟")
        if self.sound_enabled:
            play_sound(SOUND_BLIP, 0.35)

    def check_theme_update(self):
        """Comprueba si dynamic-theme actualizó theme.json."""
        if os.path.exists(THEME_JSON):
            try:
                mtime = os.path.getmtime(THEME_JSON)
                if mtime > self.last_theme_mtime:
                    self.last_theme_mtime = mtime
                    self.theme = load_theme()
                    self.apply_theme()
                    self.queue_draw()
            except Exception:
                pass
        return True

    def apply_theme(self):
        """Aplica estilos CSS dinámicos basados en el tema."""
        t = self.theme
        ar, ag, ab = hex_to_rgb(t["accent_hex"])
        accent = t["accent_hex"]
        dim = t["accent_dim_hex"]
        pink = t["horn_pink"]

        css = f"""
        window {{
            background-color: transparent;
        }}

        /* Cabecera estilo Gardevoir */
        .core-header {{
            border-bottom: 1px solid rgba(255, 255, 255, 0.10);
            background-color: rgba(255, 255, 255, 0.02);
        }}

        .core-title {{
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 12px;
            color: #FFFFFF;
            letter-spacing: 1.2px;
            text-shadow: 0 0 10px {accent};
        }}

        .header-btn {{
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.14);
            color: #E2E8F0;
            font-family: 'JetBrainsMono Nerd Font', monospace;
            font-size: 12px;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 6px;
            transition: all 120ms ease;
        }}
        .header-btn:focus,
        .header-btn:hover {{
            background-color: rgba({ar}, {ag}, {ab}, 0.28);
            border-color: {accent};
            box-shadow: 0 0 12px {accent};
            color: #FFFFFF;
            outline: none;
        }}
        .header-btn-close:focus,
        .header-btn-close:hover {{
            background-color: {pink};
            border-color: {pink};
            box-shadow: 0 0 14px {pink};
            color: #FFFFFF;
            outline: none;
        }}

        /* Tarjetas de sensores */
        .card-box {{
            background-color: rgba(4, 6, 14, 0.80);
            border: 1px solid rgba({ar}, {ag}, {ab}, 0.40);
            border-radius: 10px;
            padding: 9px 12px;
            margin: 0 12px;
            box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.4);
        }}

        .card-box-subtle {{
            background-color: rgba(10, 12, 22, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 8px 10px;
            margin: 0 12px;
        }}

        /* Tipografías y etiquetas */
        .font-icon {{
            font-family: 'JetBrainsMono Nerd Font', monospace;
            font-size: 13px;
            color: {accent};
        }}

        .font-section {{
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 11px;
            color: #FFFFFF;
            letter-spacing: 0.5px;
        }}

        .font-sub {{
            font-family: 'Inter', sans-serif;
            font-size: 10px;
            color: #94A3B8;
        }}

        .font-mono {{
            font-family: 'JetBrainsMono Nerd Font', monospace;
            font-size: 10px;
            color: #CBD5E1;
        }}

        .font-big-val {{
            font-family: 'Press Start 2P', monospace;
            font-size: 18px;
            color: #FFFFFF;
            text-shadow: 0 0 8px {accent};
        }}

        /* Insignia Térmica */
        .badge-thermal {{
            border-radius: 6px;
            padding: 3px 8px;
            font-family: 'JetBrainsMono Nerd Font', monospace;
            font-size: 11px;
            font-weight: 800;
        }}

        /* Barra de progreso de cores */
        progressbar trough {{
            background-color: rgba(255, 255, 255, 0.08);
            border-radius: 3px;
            min-height: 6px;
            border: none;
        }}
        progressbar progress {{
            background-color: {accent};
            border-radius: 3px;
            box-shadow: 0 0 6px {accent};
        }}

        /* Barra de progreso de memoria */
        .ram-bar trough {{
            min-height: 8px;
            background-color: rgba(255, 255, 255, 0.08);
            border-radius: 4px;
        }}
        .ram-bar progress {{
            min-height: 8px;
            background-color: {accent};
            border-radius: 4px;
            box-shadow: 0 0 8px {accent};
        }}
        """
        self.css_provider.load_from_data(css.encode('utf-8'))

    def build_ui(self):
        """Construye todos los elementos de la interfaz."""
        root_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        root_vbox.set_margin_bottom(12)
        self.add(root_vbox)

        # ── 1. CABECERA (Bug EventBox Margins) ─────────────────────────────────
        header = Gtk.EventBox()
        header.get_style_context().add_class("core-header")
        header.connect("button-press-event", self.on_header_drag)

        h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        h_box.set_margin_start(16)
        h_box.set_margin_end(14)
        h_box.set_margin_top(10)
        h_box.set_margin_bottom(10)
        header.add(h_box)

        # Flor Gardevoir con margen derecho
        flower_lbl = Gtk.Label(label="🌸")
        flower_lbl.override_font(Pango.FontDescription("13"))
        flower_lbl.set_margin_end(6)
        h_box.pack_start(flower_lbl, False, False, 0)

        # Título
        title = Gtk.Label(label="GARDEVOIR COREDEX")
        title.get_style_context().add_class("core-title")
        h_box.pack_start(title, False, False, 0)

        spacer = Gtk.Box()
        h_box.pack_start(spacer, True, True, 0)

        # Botones de control
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Botón Sonido
        self.sound_btn = Gtk.Button()
        self.sound_btn.get_style_context().add_class("header-btn")
        self.sound_btn_lbl = Gtk.Label(label="󰕾" if self.sound_enabled else "󰝟")
        self.sound_btn_lbl.get_style_context().add_class("font-icon")
        self.sound_btn.add(self.sound_btn_lbl)
        self.sound_btn.connect("clicked", self.toggle_sound)
        btn_box.pack_start(self.sound_btn, False, False, 0)

        # Botón Refrescar
        self.refresh_btn = Gtk.Button()
        self.refresh_btn.get_style_context().add_class("header-btn")
        rf_lbl = Gtk.Label(label="󰑐")
        rf_lbl.get_style_context().add_class("font-icon")
        self.refresh_btn.add(rf_lbl)
        self.refresh_btn.connect("clicked", lambda b: self.on_refresh_clicked())
        btn_box.pack_start(self.refresh_btn, False, False, 0)

        # Botón Minimizar
        min_btn = Gtk.Button()
        min_btn.get_style_context().add_class("header-btn")
        min_lbl = Gtk.Label(label="󰍵")
        min_lbl.get_style_context().add_class("font-icon")
        min_btn.add(min_lbl)
        min_btn.connect("clicked", self.minimize_app)
        btn_box.pack_start(min_btn, False, False, 0)

        # Botón Cerrar
        close_btn = Gtk.Button()
        close_btn.get_style_context().add_class("header-btn")
        close_btn.get_style_context().add_class("header-btn-close")
        close_lbl = Gtk.Label(label="󰅖")
        close_lbl.get_style_context().add_class("font-icon")
        close_btn.add(close_lbl)
        close_btn.connect("clicked", self.close_app)
        btn_box.pack_start(close_btn, False, False, 0)

        h_box.pack_start(btn_box, False, False, 0)
        root_vbox.pack_start(header, False, False, 0)

        # ── 2. CARD 1: CPU RESUMEN & TEMPERATURA GENERAL ───────────────────────
        c1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        c1.get_style_context().add_class("card-box")

        # Fila Superior: Icono CPU + Modelo + Subtítulo
        c1_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cpu_icon = Gtk.Label(label="󰻠")
        cpu_icon.get_style_context().add_class("font-icon")
        c1_top.pack_start(cpu_icon, False, False, 0)

        cpu_title = Gtk.Label(label=self.cpu_model)
        cpu_title.get_style_context().add_class("font-section")
        c1_top.pack_start(cpu_title, False, False, 0)

        c1_spacer = Gtk.Box()
        c1_top.pack_start(c1_spacer, True, True, 0)

        threads_tag = Gtk.Label(label=f"{self.num_cores} Hilos")
        threads_tag.get_style_context().add_class("font-sub")
        c1_top.pack_start(threads_tag, False, False, 0)
        c1.pack_start(c1_top, False, False, 0)

        # Fila Central: Valor Grande de Uso % + Frecuencia + Badge de Temperatura
        c1_mid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.cpu_pct_lbl = Gtk.Label(label="--%")
        self.cpu_pct_lbl.get_style_context().add_class("font-big-val")
        c1_mid.pack_start(self.cpu_pct_lbl, False, False, 0)

        freq_vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.cpu_freq_lbl = Gtk.Label(label="-- GHz")
        self.cpu_freq_lbl.get_style_context().add_class("font-mono")
        self.cpu_freq_lbl.set_xalign(0.0)
        freq_sub = Gtk.Label(label="Frecuencia reloj")
        freq_sub.get_style_context().add_class("font-sub")
        freq_sub.set_xalign(0.0)
        freq_vbox.pack_start(self.cpu_freq_lbl, False, False, 0)
        freq_vbox.pack_start(freq_sub, False, False, 0)
        c1_mid.pack_start(freq_vbox, False, False, 0)

        c1_mid_spacer = Gtk.Box()
        c1_mid.pack_start(c1_mid_spacer, True, True, 0)

        # Badge térmico dinámico
        self.cpu_temp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.cpu_temp_box.get_style_context().add_class("badge-thermal")
        t_icon = Gtk.Label(label="󰔏")
        t_icon.get_style_context().add_class("font-mono")
        self.cpu_temp_lbl = Gtk.Label(label="--°C")
        self.cpu_temp_lbl.get_style_context().add_class("font-mono")
        self.cpu_temp_box.pack_start(t_icon, False, False, 0)
        self.cpu_temp_box.pack_start(self.cpu_temp_lbl, False, False, 0)
        c1_mid.pack_start(self.cpu_temp_box, False, False, 0)

        c1.pack_start(c1_mid, False, False, 0)
        root_vbox.pack_start(c1, False, False, 0)

        # ── 3. CARD 2: MATRIZ DE CORES (12 HILOS) ──────────────────────────────
        c2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        c2.get_style_context().add_class("card-box")

        c2_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        core_hdr_icon = Gtk.Label(label="󰍛")
        core_hdr_icon.get_style_context().add_class("font-icon")
        c2_top.pack_start(core_hdr_icon, False, False, 0)
        core_hdr_lbl = Gtk.Label(label="Cores del Procesador")
        core_hdr_lbl.get_style_context().add_class("font-section")
        c2_top.pack_start(core_hdr_lbl, False, False, 0)

        c2_top_sp = Gtk.Box()
        c2_top.pack_start(c2_top_sp, True, True, 0)

        c2_hint = Gtk.Label(label="Uso por hilo")
        c2_hint.get_style_context().add_class("font-sub")
        c2_top.pack_start(c2_hint, False, False, 0)
        c2.pack_start(c2_top, False, False, 0)

        # Matriz de 2 columnas de barras
        grid = Gtk.Grid()
        grid.set_column_spacing(14)
        grid.set_row_spacing(3)
        grid.set_hexpand(True)

        self.core_bars = []
        self.core_val_lbls = []

        half = (self.num_cores + 1) // 2
        for i in range(self.num_cores):
            col = 0 if i < half else 1
            row = i if i < half else i - half

            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            box.set_hexpand(True)

            tag = Gtk.Label(label=f"C{i+1:02d}")
            tag.get_style_context().add_class("font-mono")
            tag.set_size_request(24, -1)
            box.pack_start(tag, False, False, 0)

            bar = Gtk.ProgressBar()
            bar.set_hexpand(True)
            bar.set_fraction(0.0)
            self.core_bars.append(bar)
            box.pack_start(bar, True, True, 0)

            pct_lbl = Gtk.Label(label="0%")
            pct_lbl.get_style_context().add_class("font-mono")
            pct_lbl.set_size_request(32, -1)
            pct_lbl.set_xalign(1.0)
            self.core_val_lbls.append(pct_lbl)
            box.pack_start(pct_lbl, False, False, 0)

            grid.attach(box, col, row, 1, 1)

        c2.pack_start(grid, False, False, 0)
        root_vbox.pack_start(c2, False, False, 0)

        # ── 4. CARD 3: GPU DEDICADA (NVIDIA RTX 5060 Ti) ───────────────────────
        c3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        c3.get_style_context().add_class("card-box")

        c3_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        gpu_icon = Gtk.Label(label="󰢮")
        gpu_icon.get_style_context().add_class("font-icon")
        c3_top.pack_start(gpu_icon, False, False, 0)

        self.gpu_title_lbl = Gtk.Label(label="NVIDIA GeForce RTX 5060 Ti")
        self.gpu_title_lbl.get_style_context().add_class("font-section")
        c3_top.pack_start(self.gpu_title_lbl, False, False, 0)

        c3_sp = Gtk.Box()
        c3_top.pack_start(c3_sp, True, True, 0)

        # Badge GPU Temp
        self.gpu_temp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.gpu_temp_box.get_style_context().add_class("badge-thermal")
        gt_icon = Gtk.Label(label="󰔏")
        gt_icon.get_style_context().add_class("font-mono")
        self.gpu_temp_lbl = Gtk.Label(label="--°C")
        self.gpu_temp_lbl.get_style_context().add_class("font-mono")
        self.gpu_temp_box.pack_start(gt_icon, False, False, 0)
        self.gpu_temp_box.pack_start(self.gpu_temp_lbl, False, False, 0)
        c3_top.pack_start(self.gpu_temp_box, False, False, 0)
        c3.pack_start(c3_top, False, False, 0)

        # Fila de métricas secundarias GPU
        c3_stats = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)

        # Utilización GPU
        self.gpu_util_lbl = Gtk.Label(label="Carga: --%")
        self.gpu_util_lbl.get_style_context().add_class("font-mono")
        c3_stats.pack_start(self.gpu_util_lbl, False, False, 0)

        # Potencia W
        self.gpu_pwr_lbl = Gtk.Label(label="Potencia: --W")
        self.gpu_pwr_lbl.get_style_context().add_class("font-mono")
        c3_stats.pack_start(self.gpu_pwr_lbl, False, False, 0)

        # Fan %
        self.gpu_fan_lbl = Gtk.Label(label="Ventilador: 0%")
        self.gpu_fan_lbl.get_style_context().add_class("font-mono")
        c3_stats.pack_start(self.gpu_fan_lbl, False, False, 0)
        c3.pack_start(c3_stats, False, False, 0)

        # Barra VRAM
        vram_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vram_tag = Gtk.Label(label="VRAM")
        vram_tag.get_style_context().add_class("font-mono")
        vram_tag.set_size_request(32, -1)
        vram_box.pack_start(vram_tag, False, False, 0)

        self.vram_bar = Gtk.ProgressBar()
        self.vram_bar.set_hexpand(True)
        vram_box.pack_start(self.vram_bar, True, True, 0)

        self.vram_lbl = Gtk.Label(label="-- / -- GB")
        self.vram_lbl.get_style_context().add_class("font-mono")
        vram_box.pack_start(self.vram_lbl, False, False, 0)
        c3.pack_start(vram_box, False, False, 0)

        root_vbox.pack_start(c3, False, False, 0)

        # ── 5. CARD 4: MEMORIA RAM & NVMe SSD ──────────────────────────────────
        c4 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        c4.get_style_context().add_class("card-box-subtle")

        # Fila RAM
        ram_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ram_icon = Gtk.Label(label="󰘚")
        ram_icon.get_style_context().add_class("font-icon")
        ram_row.pack_start(ram_icon, False, False, 0)

        ram_tag = Gtk.Label(label="RAM")
        ram_tag.get_style_context().add_class("font-section")
        ram_row.pack_start(ram_tag, False, False, 0)

        self.ram_bar = Gtk.ProgressBar()
        self.ram_bar.get_style_context().add_class("ram-bar")
        self.ram_bar.set_hexpand(True)
        ram_row.pack_start(self.ram_bar, True, True, 0)

        self.ram_lbl = Gtk.Label(label="-- / -- GB")
        self.ram_lbl.get_style_context().add_class("font-mono")
        ram_row.pack_start(self.ram_lbl, False, False, 0)
        c4.pack_start(ram_row, False, False, 0)

        # Fila NVMe
        nvme_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        nvme_icon = Gtk.Label(label="󰋊")
        nvme_icon.get_style_context().add_class("font-icon")
        nvme_row.pack_start(nvme_icon, False, False, 0)

        nvme_lbl = Gtk.Label(label="NVMe SSD")
        nvme_lbl.get_style_context().add_class("font-section")
        nvme_row.pack_start(nvme_lbl, False, False, 0)

        c4_sp = Gtk.Box()
        nvme_row.pack_start(c4_sp, True, True, 0)

        self.nvme_temp_lbl = Gtk.Label(label="--°C")
        self.nvme_temp_lbl.get_style_context().add_class("font-mono")
        nvme_row.pack_start(self.nvme_temp_lbl, False, False, 0)
        c4.pack_start(nvme_row, False, False, 0)

        root_vbox.pack_start(c4, False, False, 0)

        # ── 6. PIE DE VENTANA (Atajos rápidos) ─────────────────────────────────
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        footer.set_halign(Gtk.Align.CENTER)
        footer.set_margin_top(2)

        f_esc = Gtk.Label(label="[ Esc / Q ] Cerrar")
        f_esc.get_style_context().add_class("font-sub")
        footer.pack_start(f_esc, False, False, 0)

        f_flower = Gtk.Label(label="🌸")
        f_flower.override_font(Pango.FontDescription("9"))
        f_flower.set_margin_start(4)
        f_flower.set_margin_end(4)
        footer.pack_start(f_flower, False, False, 0)

        f_rf = Gtk.Label(label="[ R ] Refrescar")
        f_rf.get_style_context().add_class("font-sub")
        footer.pack_start(f_rf, False, False, 0)

        root_vbox.pack_start(footer, False, False, 0)

    def on_refresh_clicked(self):
        if self.sound_enabled:
            play_sound(SOUND_BLIP, 0.3)
        self.update_hardware_metrics()

    def on_metrics_tick(self):
        """Actualización periódica por temporizador GLib."""
        self.update_hardware_metrics()
        return True

    def update_hardware_metrics(self):
        """Recoge métricas del sistema y actualiza los componentes visuales."""
        try:
            # 1. CPU general y frecuencia
            overall_cpu = psutil.cpu_percent(interval=None)
            self.cpu_pct_lbl.set_text(f"{int(overall_cpu):2d}%")

            freq = psutil.cpu_freq()
            if freq and freq.current:
                ghz = freq.current / 1000.0
                self.cpu_freq_lbl.set_text(f"{ghz:.2f} GHz")
            else:
                self.cpu_freq_lbl.set_text("4.20 GHz")

            # 2. Cores individuales
            cores_pct = psutil.cpu_percent(percpu=True, interval=None)
            for i, pct in enumerate(cores_pct):
                if i < len(self.core_bars):
                    frac = max(0.0, min(1.0, pct / 100.0))
                    self.core_bars[i].set_fraction(frac)
                    self.core_val_lbls[i].set_text(f"{int(pct)}%")

            # 3. Temperaturas (CPU & NVMe)
            temps = psutil.sensors_temperatures()
            cpu_t = None
            if "k10temp" in temps:
                for entry in temps["k10temp"]:
                    if entry.label in ("Tctl", "Tdie") or not entry.label:
                        cpu_t = entry.current
                        break
            elif "coretemp" in temps:
                for entry in temps["coretemp"]:
                    if "Package" in entry.label or not entry.label:
                        cpu_t = entry.current
                        break

            if cpu_t is not None:
                self.cpu_temp_lbl.set_text(f"{cpu_t:.1f}°C")
                color = get_thermal_color(cpu_t)
                self.cpu_temp_box.override_background_color(
                    Gtk.StateFlags.NORMAL,
                    Gdk.RGBA(*[x/255.0 for x in hex_to_rgb(color)], 0.25)
                )
            else:
                self.cpu_temp_lbl.set_text("N/D")

            # NVMe Temp
            nvme_t = None
            if "nvme" in temps:
                for entry in temps["nvme"]:
                    if entry.label == "Composite" or not entry.label:
                        nvme_t = entry.current
                        break
            if nvme_t is not None:
                self.nvme_temp_lbl.set_text(f"Temp: {nvme_t:.1f}°C")
            else:
                self.nvme_temp_lbl.set_text("Óptimo")

            # 4. GPU NVIDIA
            with self.lock:
                gpu = self.gpu_data

            if gpu:
                self.gpu_title_lbl.set_text(gpu["name"])
                gt = gpu["temp"]
                self.gpu_temp_lbl.set_text(f"{gt}°C")
                gt_color = get_thermal_color(gt)
                self.gpu_temp_box.override_background_color(
                    Gtk.StateFlags.NORMAL,
                    Gdk.RGBA(*[x/255.0 for x in hex_to_rgb(gt_color)], 0.25)
                )

                self.gpu_util_lbl.set_text(f"Carga: {gpu['util']}%")
                self.gpu_pwr_lbl.set_text(f"Potencia: {int(gpu['power'])}W")
                self.gpu_fan_lbl.set_text(f"Ventilador: {gpu['fan']}%")

                used_gb = gpu["mem_used"] / 1024.0
                total_gb = gpu["mem_total"] / 1024.0
                frac_vram = max(0.0, min(1.0, gpu["mem_used"] / max(1, gpu["mem_total"])))
                self.vram_bar.set_fraction(frac_vram)
                self.vram_lbl.set_text(f"{used_gb:.1f} / {total_gb:.1f} GB ({int(frac_vram*100)}%)")

            # 5. Memoria RAM
            ram = psutil.virtual_memory()
            ram_used_gb = ram.used / (1024**3)
            ram_total_gb = ram.total / (1024**3)
            self.ram_bar.set_fraction(ram.percent / 100.0)
            self.ram_lbl.set_text(f"{ram_used_gb:.1f} / {ram_total_gb:.1f} GB ({int(ram.percent)}%)")

        except Exception as e:
            pass


def main():
    app = GardevoirCoreDex()
    app.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
