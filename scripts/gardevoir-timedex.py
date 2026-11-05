#!/usr/bin/env python3
"""
🌸 Gardevoir TimeDex - Suite de Gestión del Tiempo (Reloj, Timer, Cronómetro, Alarmas)
Personalizada para Arch Linux + Cinnamon con estética Glassmorphism Obsidian a 88%,
tipografía retro 'Press Start 2P', integración con dynamic-theme.py, sonidos en bucle
continuo, maximización automática al sonar y soporte para MP3 personalizados.
"""

import os
import sys
import time
import json
import math
import shutil
import subprocess
import datetime
import zoneinfo
from pathlib import Path

import warnings
warnings.filterwarnings('ignore')

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango
import cairo

HOME = str(Path.home())
CONFIG_DIR = os.path.join(HOME, ".config/gardevoir-timedex")
THEME_JSON = os.path.join(CONFIG_DIR, "theme.json")
CONFIG_JSON = os.path.join(CONFIG_DIR, "config.json")
ALARMS_JSON = os.path.join(CONFIG_DIR, "alarms.json")

SOUND_DIR = os.path.join(HOME, ".local/share/sounds/pokemon")
SOUND_BLIP = os.path.join(SOUND_DIR, "pokeball_blip.wav")
SOUND_HEAL = os.path.join(SOUND_DIR, "pokemon_center_heal.wav")
SOUND_ITEM = os.path.join(SOUND_DIR, "item_get.wav")
SOUND_ALARM_DEFAULT = os.path.join(SOUND_DIR, "Ultra_Necrozma_Gardevoir_Alarm.mp3")
AVATAR_FILE = os.path.join(HOME, ".local/share/gardevoir-greeter/avatar.png")

PRESET_CITIES = [
    ("Asia/Tokyo", "Tokio (Japón)"),
    ("Europe/Madrid", "Madrid (España)"),
    ("America/New_York", "Nueva York (EE. UU.)"),
    ("Europe/London", "Londres (Reino Unido)"),
    ("Europe/Paris", "París (Francia)"),
    ("Europe/Berlin", "Berlín (Alemania)"),
    ("Europe/Rome", "Roma (Italia)"),
    ("America/Los_Angeles", "Los Ángeles (EE. UU.)"),
    ("America/Chicago", "Chicago (EE. UU.)"),
    ("America/Toronto", "Toronto (Canadá)"),
    ("America/Argentina/Buenos_Aires", "Buenos Aires (Argentina)"),
    ("America/Santiago", "Santiago (Chile)"),
    ("America/Bogota", "Bogotá (Colombia)"),
    ("America/Lima", "Lima (Perú)"),
    ("America/Sao_Paulo", "São Paulo (Brasil)"),
    ("America/Caracas", "Caracas (Venezuela)"),
    ("America/Mexico_City", "Ciudad de México (México)"),
    ("Asia/Seoul", "Seúl (Corea del Sur)"),
    ("Asia/Shanghai", "Pekín / Shanghái (China)"),
    ("Asia/Singapore", "Singapur"),
    ("Asia/Dubai", "Dubái (Emiratos Árabes)"),
    ("Asia/Kolkata", "Nueva Delhi (India)"),
    ("Australia/Sydney", "Sídney (Australia)"),
    ("Pacific/Auckland", "Auckland (Nueva Zelanda)"),
    ("Pacific/Honolulu", "Honolulú (Hawái, EE. UU.)"),
    ("UTC", "Tiempo Universal Coordinado (UTC)")
]


def play_sound(sound_path=SOUND_BLIP, volume=0.4):
    """Reproduce un efecto de sonido corto de forma segura."""
    if os.path.exists(sound_path):
        try:
            subprocess.Popen(
                ["pw-play", f"--volume={volume}", sound_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass


def start_alarm_audio_loop(sound_file):
    """Inicia reproducción en bucle continuo de la alarma (MP3, WAV u OGG) hasta ser detenida."""
    if not sound_file or not os.path.exists(sound_file):
        sound_file = SOUND_ALARM_DEFAULT if os.path.exists(SOUND_ALARM_DEFAULT) else SOUND_HEAL

    cmd = []
    if sound_file.lower().endswith(".mp3"):
        if shutil.which("mpg123"):
            cmd = ["mpg123", "-q", "--loop", "-1", sound_file]
        else:
            cmd = ["ffplay", "-nodisp", "-loop", "0", "-volume", "100", sound_file]
    else:
        if shutil.which("ffplay"):
            cmd = ["ffplay", "-nodisp", "-loop", "0", "-volume", "100", sound_file]
        else:
            cmd = ["bash", "-c", f"while true; do pw-play --volume=0.85 '{sound_file}'; sleep 0.2; done"]

    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return proc
    except Exception as e:
        print(f"Error iniciando audio de alarma: {e}")
        return None


def load_theme():
    defaults = {
        "dom_hex": "#141228",
        "accent_hex": "#4f33c7",
        "accent_dim_hex": "#271a63",
        "horn_pink": "#FF4370",
        "text_white": "#FFFFFF",
        "text_muted": "#CBD5E1"
    }
    for p in [THEME_JSON, os.path.join(HOME, ".config/gardevoir-calc/theme.json")]:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    defaults.update(json.load(f))
                    break
            except Exception:
                pass
    return defaults


def load_config():
    defaults = {
        "sound": True,
        "default_tab": 3,
        "alarm_sound_path": SOUND_ALARM_DEFAULT if os.path.exists(SOUND_ALARM_DEFAULT) else SOUND_HEAL,
        "world_clocks": [
            {"name": "Tokio (Japón)", "tz": "Asia/Tokyo"},
            {"name": "Madrid (España)", "tz": "Europe/Madrid"},
            {"name": "Nueva York (EE. UU.)", "tz": "America/New_York"}
        ]
    }
    if os.path.exists(CONFIG_JSON):
        try:
            with open(CONFIG_JSON, "r") as f:
                defaults.update(json.load(f))
        except Exception:
            pass
    if "world_clocks" not in defaults or not isinstance(defaults["world_clocks"], list):
        defaults["world_clocks"] = [
            {"name": "Tokio (Japón)", "tz": "Asia/Tokyo"},
            {"name": "Madrid (España)", "tz": "Europe/Madrid"},
            {"name": "Nueva York (EE. UU.)", "tz": "America/New_York"}
        ]
    return defaults


def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_JSON, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def load_alarms():
    if os.path.exists(ALARMS_JSON):
        try:
            with open(ALARMS_JSON, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_alarms(alarms):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(ALARMS_JSON, "w") as f:
            json.dump(alarms, f, indent=2)
    except Exception:
        pass


def hex_to_rgb(hex_str):
    h = hex_str.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


class GardevoirTimeDex(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("Gardevoir TimeDex")
        self.set_wmclass("gardevoir-timedex", "GardevoirTimeDex")
        self.set_role("gardevoir-timedex")
        self.set_default_size(390, 560)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Transparencia RGBA
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.connect("draw", self.on_draw)

        # Configuración y temas
        self.config = load_config()
        self.theme = load_theme()
        self.alarms = load_alarms()
        self.last_theme_mtime = os.path.getmtime(THEME_JSON) if os.path.exists(THEME_JSON) else 0

        # Estados de los módulos
        # 1. Temporizador
        self.timer_seconds = 300
        self.timer_initial = 300
        self.timer_running = False
        self.timer_glib_id = None

        # 2. Cronómetro
        self.chrono_running = False
        self.chrono_start_time = 0.0
        self.chrono_elapsed = 0.0
        self.chrono_glib_id = None
        self.chrono_laps = []

        # 3. Alarmas y Timbrado Activo
        self.fired_alarm_keys = set()
        self.last_check_minute = ""
        self.ringing_process = None
        self.is_ringing = False
        self.previous_tab = 0

        # 4. Reloj y Horas Mundiales (100% Offline IANA)
        self.world_clocks = list(self.config.get("world_clocks", []))
        self.world_clock_widgets = []

        # Proveedor de CSS
        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(
            screen, self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.apply_theme()

        # Construir Interfaz
        self.build_ui()

        # Atajos de teclado internos
        self.connect("key-press-event", self.on_key_press)

        # Timers periódicos
        GLib.timeout_add(1000, self.on_clock_tick)
        GLib.timeout_add(2000, self.check_theme_update)
        GLib.timeout_add_seconds(60, self.refresh_weather_tick)

        if self.config.get("sound", True):
            play_sound(SOUND_BLIP, volume=0.35)

    def on_draw(self, widget, cr):
        alloc = widget.get_allocation()
        w, h = alloc.width, alloc.height

        # Limpiar canvas con transparencia completa
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        # Trazar rectángulo redondeado
        cr.set_operator(cairo.OPERATOR_OVER)
        radius = 16.0
        degrees = math.pi / 180.0

        cr.new_sub_path()
        cr.arc(w - radius, radius, radius, -90 * degrees, 0 * degrees)
        cr.arc(w - radius, h - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc(radius, h - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc(radius, radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path()

        # Fondo Cristal Ahumado (88% opacidad)
        t = self.theme
        dr, dg, db = hex_to_rgb(t["dom_hex"])
        bg_r = max(0.03, (dr / 255.0) * 0.6)
        bg_g = max(0.04, (dg / 255.0) * 0.6)
        bg_b = max(0.08, (db / 255.0) * 0.7)
        cr.set_source_rgba(bg_r, bg_g, bg_b, 0.88)
        cr.fill_preserve()

        # Borde Neón Dinámico (o Rosa pulsante si está sonando)
        if self.is_ringing:
            pr, pg, pb = hex_to_rgb(t["horn_pink"])
            cr.set_source_rgba(pr / 255.0, pg / 255.0, pb / 255.0, 0.95)
            cr.set_line_width(2.5)
        else:
            ar, ag, ab = hex_to_rgb(t["accent_hex"])
            cr.set_source_rgba(ar / 255.0, ag / 255.0, ab / 255.0, 0.95)
            cr.set_line_width(1.5)

        cr.stroke()
        return False

    def apply_theme(self):
        t = self.theme
        ar, ag, ab = hex_to_rgb(t["accent_hex"])
        accent = t["accent_hex"]
        pink = t["horn_pink"]

        css = f"""
        window {{
            background-color: transparent;
        }}

        .calc-header {{
            padding: 10px 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.10);
            background-color: rgba(255, 255, 255, 0.02);
        }}

        .calc-title {{
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
            font-family: 'JetBrainsMono Nerd Font', 'Inter', monospace;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 6px;
            transition: all 120ms ease;
        }}
        .header-btn:focus,
        .header-btn:hover {{
            background-color: rgba(255, 255, 255, 0.22);
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

        /* Barra de Pestañas & Dónde estás parado */
        .tab-box {{
            padding: 8px 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }}
        .tab-btn {{
            font-family: 'JetBrainsMono Nerd Font', 'Inter', sans-serif;
            font-size: 11px;
            font-weight: 700;
            color: #94A3B8;
            background-color: rgba(255, 255, 255, 0.04);
            background-image: none;
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom: 3.5px solid transparent;
            border-radius: 8px;
            padding: 7px 10px;
            transition: all 120ms ease;
        }}
        /* DONDE ESTÁS PARADO: Foco de teclado y Hover */
        .tab-btn:focus,
        .tab-btn:hover {{
            background-color: rgba({ar}, {ag}, {ab}, 0.20);
            border: 1px solid rgba({ar}, {ag}, {ab}, 0.60);
            border-bottom: 3.5px solid {accent};
            color: #FFFFFF;
            box-shadow: 0 0 16px rgba({ar}, {ag}, {ab}, 0.85), inset 0 0 8px rgba({ar}, {ag}, {ab}, 0.35);
            outline: none;
        }}
        /* Pestaña Seleccionada Activa */
        .tab-btn-active {{
            background-color: rgba({ar}, {ag}, {ab}, 0.35);
            background-image: none;
            border: 1px solid {accent};
            border-bottom: 4px solid {accent};
            color: #FFFFFF;
            font-weight: 800;
            text-shadow: 0 0 12px {accent}, 0 0 24px {accent};
            box-shadow: 0 5px 22px rgba({ar}, {ag}, {ab}, 0.95), inset 0 0 14px rgba({ar}, {ag}, {ab}, 0.45);
        }}
        .tab-btn-active:focus,
        .tab-btn-active:hover {{
            box-shadow: 0 5px 28px {accent}, inset 0 0 18px rgba({ar}, {ag}, {ab}, 0.60);
            outline: none;
        }}

        /* Pantallas Display */
        .display-card {{
            background-color: rgba(4, 6, 12, 0.88);
            border: 1px solid rgba({ar}, {ag}, {ab}, 0.50);
            border-radius: 12px;
            margin: 12px 14px 6px 14px;
            padding: 14px;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5);
        }}

        .display-number {{
            font-family: 'Press Start 2P', monospace;
            font-size: 26px;
            color: #FFFFFF;
            text-shadow: 0 0 12px {accent}, 0 0 24px {accent}, 0 0 36px rgba({ar}, {ag}, {ab}, 0.85);
            padding: 8px 0;
        }}

        .display-sub {{
            font-family: 'JetBrainsMono Nerd Font', monospace;
            font-size: 11px;
            color: #94A3B8;
        }}

        /* Barra de Progreso */
        progressbar trough {{
            background-color: rgba(255, 255, 255, 0.08);
            border-radius: 4px;
            min-height: 8px;
            border: none;
        }}
        progressbar progress {{
            background-color: {accent};
            border-radius: 4px;
            box-shadow: 0 0 8px {accent};
        }}

        /* Botones de acción */
        .action-btn {{
            font-family: 'JetBrainsMono Nerd Font', 'Inter', monospace;
            font-size: 13px;
            font-weight: 800;
            color: #FFFFFF;
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 8px;
            padding: 8px 14px;
            min-height: 42px;
            transition: all 120ms ease;
        }}
        .action-btn:focus,
        .action-btn:hover {{
            background-color: rgba({ar}, {ag}, {ab}, 0.28);
            border-color: {accent};
            box-shadow: 0 0 14px rgba({ar}, {ag}, {ab}, 0.80), inset 0 0 8px rgba({ar}, {ag}, {ab}, 0.35);
            outline: none;
        }}
        .action-btn-primary {{
            background-color: {accent};
            border-color: {accent};
            color: #FFFFFF;
            box-shadow: 0 0 10px rgba({ar}, {ag}, {ab}, 0.45);
        }}
        .action-btn-primary:focus,
        .action-btn-primary:hover {{
            box-shadow: 0 0 20px {accent}, inset 0 0 10px rgba(255, 255, 255, 0.3);
            outline: none;
        }}
        .action-btn-pink {{
            background-color: rgba(255, 67, 112, 0.35);
            border-color: {pink};
            color: #FFFFFF;
        }}
        .action-btn-pink:focus,
        .action-btn-pink:hover {{
            background-color: {pink};
            box-shadow: 0 0 16px {pink};
            outline: none;
        }}

        /* Pantalla de Timbrado / Ringing */
        .ringing-card {{
            background-color: rgba(10, 4, 12, 0.94);
            border: 2px solid {pink};
            border-radius: 14px;
            padding: 24px;
            margin: 20px;
            box-shadow: 0 0 30px rgba(255, 67, 112, 0.5);
        }}
        .ringing-title {{
            font-family: 'Press Start 2P', monospace;
            font-size: 22px;
            color: #FFFFFF;
            text-shadow: 0 0 14px {pink}, 0 0 28px {pink};
        }}
        .btn-stop-alarm {{
            background-color: {pink};
            border: 2px solid #FFFFFF;
            color: #FFFFFF;
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            font-weight: 900;
            letter-spacing: 1px;
            padding: 14px 28px;
            border-radius: 12px;
            box-shadow: 0 0 20px {pink};
            transition: all 150ms ease;
        }}
        .btn-stop-alarm:focus,
        .btn-stop-alarm:hover {{
            background-color: #ff1f58;
            box-shadow: 0 0 30px #FF4370;
            outline: none;
        }}

        /* Presets Rápidos */
        .preset-btn {{
            font-family: 'JetBrainsMono Nerd Font', monospace;
            font-size: 11px;
            font-weight: 700;
            color: {accent};
            background-color: rgba({ar}, {ag}, {ab}, 0.12);
            border: 1px solid rgba({ar}, {ag}, {ab}, 0.35);
            border-radius: 6px;
            padding: 6px 10px;
            min-height: 36px;
            transition: all 120ms ease;
        }}
        .preset-btn:focus,
        .preset-btn:hover {{
            background-color: rgba({ar}, {ag}, {ab}, 0.30);
            border-color: {accent};
            box-shadow: 0 0 14px {accent}, inset 0 0 6px rgba({ar}, {ag}, {ab}, 0.35);
            color: #FFFFFF;
            outline: none;
        }}

        /* Switches / Interruptores temáticos */
        switch {{
            background-color: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.20);
            border-radius: 14px;
            box-shadow: none;
        }}
        switch:checked {{
            background-color: {accent};
            border-color: {accent};
            box-shadow: 0 0 10px rgba({ar}, {ag}, {ab}, 0.55);
        }}
        switch slider {{
            background-color: #FFFFFF;
            border-radius: 14px;
            border: none;
        }}

        .list-card {{
            background-color: rgba(6, 10, 18, 0.70);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 9px;
            padding: 10px 12px;
            margin-bottom: 6px;
        }}

        entry, spinbutton {{
            background-color: rgba(6, 10, 18, 0.85);
            color: #FFFFFF;
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 6px;
            padding: 6px 10px;
            font-family: 'JetBrainsMono Nerd Font', monospace;
            font-size: 12px;
            min-height: 36px;
            transition: all 120ms ease;
        }}
        entry:focus, spinbutton:focus {{
            border-color: {accent};
            box-shadow: 0 0 12px {accent}, inset 0 0 4px rgba({ar}, {ag}, {ab}, 0.35);
            outline: none;
        }}

        /* Desplegables de Horas Mundiales (ComboBox) */
        combobox,
        combobox button {{
            background-color: rgba(6, 10, 18, 0.85);
            color: #FFFFFF;
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 6px;
            font-family: 'Inter', sans-serif;
            font-size: 11px;
            min-height: 36px;
            transition: all 120ms ease;
        }}
        combobox:focus,
        combobox button:focus,
        combobox:hover,
        combobox button:hover {{
            border-color: {accent};
            box-shadow: 0 0 12px {accent}, inset 0 0 4px rgba({ar}, {ag}, {ab}, 0.35);
            outline: none;
        }}
        combobox window menu,
        combobox menu {{
            background-color: rgba(14, 18, 28, 0.98);
            border: 1px solid {accent};
            border-radius: 8px;
            color: #FFFFFF;
            padding: 4px;
        }}
        combobox menu menuitem {{
            padding: 6px 10px;
            border-radius: 4px;
            color: #E2E8F0;
        }}
        combobox menu menuitem:hover {{
            background-color: {accent};
            color: #FFFFFF;
        }}
        """
        self.css_provider.load_from_data(css.encode('utf-8'))

    def check_theme_update(self):
        if os.path.exists(THEME_JSON):
            mtime = os.path.getmtime(THEME_JSON)
            if mtime > self.last_theme_mtime:
                self.last_theme_mtime = mtime
                self.theme = load_theme()
                self.apply_theme()
                self.queue_draw()
        return True

    def build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(main_box)

        # 1. Cabecera Personalizada
        header = Gtk.EventBox()
        header.get_style_context().add_class("calc-header")
        header.connect("button-press-event", self.on_header_drag)

        h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        h_box.set_margin_start(16)
        h_box.set_margin_end(14)
        h_box.set_margin_top(10)
        h_box.set_margin_bottom(10)
        header.add(h_box)

        # Icono de Gardevoir (Flor 🌸)
        flower_lbl = Gtk.Label(label="🌸")
        flower_lbl.override_font(Pango.FontDescription("13"))
        flower_lbl.set_margin_end(6)
        h_box.pack_start(flower_lbl, False, False, 0)

        title = Gtk.Label(label="GARDEVOIR TIMEDEX")
        title.get_style_context().add_class("calc-title")
        h_box.pack_start(title, False, False, 0)

        h_spacer = Gtk.Box()
        h_box.pack_start(h_spacer, True, True, 0)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        snd_icon = "󰕾" if self.config.get("sound", True) else "󰝟"
        self.btn_sound = Gtk.Button(label=snd_icon)
        self.btn_sound.get_style_context().add_class("header-btn")
        self.btn_sound.set_tooltip_text("Sonidos Pokémon [Tecla S]")
        self.btn_sound.connect("clicked", self.toggle_sound)
        btn_box.pack_start(self.btn_sound, False, False, 0)

        btn_min = Gtk.Button(label="󰍵")
        btn_min.get_style_context().add_class("header-btn")
        btn_min.set_tooltip_text("Minimizar")
        btn_min.connect("clicked", lambda b: self.iconify())
        btn_box.pack_start(btn_min, False, False, 0)

        btn_close = Gtk.Button(label="󰅖")
        btn_close.get_style_context().add_class("header-btn")
        btn_close.get_style_context().add_class("header-btn-close")
        btn_close.set_tooltip_text("Cerrar aplicación [Escape]")
        btn_close.connect("clicked", lambda b: self.destroy())
        btn_box.pack_start(btn_close, False, False, 0)

        h_box.pack_start(btn_box, False, False, 0)

        main_box.pack_start(header, False, False, 0)

        # 2. Pestañas de Navegación
        self.nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.nav_box.get_style_context().add_class("tab-box")

        self.tab_buttons = []
        tabs_info = [
            ("󰔛  Timer", 0),
            ("󰔚  Crono", 1),
            ("󰀠  Alarmas", 2),
            ("󰥔  Reloj", 3)
        ]

        for text, idx in tabs_info:
            btn = Gtk.Button(label=text)
            btn.get_style_context().add_class("tab-btn")
            btn.connect("clicked", lambda b, i=idx: self.switch_tab(i))
            self.nav_box.pack_start(btn, True, True, 0)
            self.tab_buttons.append(btn)

        main_box.pack_start(self.nav_box, False, False, 0)

        # 3. Stack de Contenido
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_transition_duration(150)
        main_box.pack_start(self.stack, True, True, 0)

        # Crear módulos
        self.build_timer_view()
        self.build_chrono_view()
        self.build_alarms_view()
        self.build_clock_view()
        self.build_ringing_view()

        # Activar pestaña por defecto
        self.switch_tab(self.config.get("default_tab", 0))

    # --- NAVEGACIÓN ---
    def switch_tab(self, idx):
        if self.is_ringing:
            return
        self.previous_tab = idx
        self.stack.set_visible_child_name(f"tab_{idx}")
        for i, btn in enumerate(self.tab_buttons):
            if i == idx:
                btn.get_style_context().add_class("tab-btn-active")
            else:
                btn.get_style_context().remove_class("tab-btn-active")
        self.config["default_tab"] = idx
        save_config(self.config)

    def on_header_drag(self, widget, event):
        if event.button == 1:
            self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def toggle_sound(self, btn=None):
        new_st = not self.config.get("sound", True)
        self.config["sound"] = new_st
        self.btn_sound.set_label("󰕾" if new_st else "󰝟")
        save_config(self.config)

    # =========================================================================
    # PANTALLA DE ALARMA ACTIVA (RINGING VIEW - MAXIMIZADA)
    # =========================================================================
    def build_ringing_view(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        vbox.set_valign(Gtk.Align.CENTER)
        vbox.set_halign(Gtk.Align.CENTER)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        card.get_style_context().add_class("ringing-card")

        self.ring_icon_label = Gtk.Label(label="󰀠")
        self.ring_icon_label.override_font(Pango.FontDescription("JetBrainsMono Nerd Font 48"))
        card.pack_start(self.ring_icon_label, False, False, 0)

        self.ring_title_label = Gtk.Label(label="¡ALARMA ACTIVADA!")
        self.ring_title_label.get_style_context().add_class("ringing-title")
        card.pack_start(self.ring_title_label, False, False, 0)

        self.ring_sub_label = Gtk.Label(label="Recordatorio")
        self.ring_sub_label.override_font(Pango.FontDescription("Inter Bold 16"))
        self.ring_sub_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 0.9))
        card.pack_start(self.ring_sub_label, False, False, 0)

        self.ring_time_label = Gtk.Label(label="--:--")
        self.ring_time_label.override_font(Pango.FontDescription("Press Start 2P 20"))
        self.ring_time_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 0.26, 0.44, 1))
        card.pack_start(self.ring_time_label, False, False, 6)

        btn_stop = Gtk.Button(label="󰓛 DETENER ALARMA")
        btn_stop.get_style_context().add_class("btn-stop-alarm")
        btn_stop.connect("clicked", lambda b: self.stop_ringing())
        card.pack_start(btn_stop, False, False, 10)

        hint = Gtk.Label(label="Presiona Espacio o Escape para detener")
        hint.get_style_context().add_class("display-sub")
        card.pack_start(hint, False, False, 0)

        vbox.pack_start(card, True, True, 0)
        self.stack.add_named(vbox, "tab_ringing")

    def trigger_alarm_alert(self, title_text, sub_text, icon_str="󰀠"):
        """Dispara la alarma: maximiza la ventana, inicia bucle de audio y muestra el botón gigante de detener."""
        self.is_ringing = True
        self.ring_title_label.set_text(title_text)
        self.ring_sub_label.set_text(sub_text)
        self.ring_icon_label.set_text(icon_str)
        self.ring_time_label.set_text(datetime.datetime.now().strftime("%H:%M:%S"))

        # Ocultar barra de pestañas durante timbrado
        self.nav_box.set_visible(False)
        self.stack.set_visible_child_name("tab_ringing")

        # Iniciar reproducción en bucle continuo
        sound_path = self.config.get("alarm_sound_path", SOUND_ALARM_DEFAULT if os.path.exists(SOUND_ALARM_DEFAULT) else SOUND_HEAL)
        if self.config.get("sound", True):
            self.stop_ringing_audio()
            self.ringing_process = start_alarm_audio_loop(sound_path)

        # Notificación desktop de alta prioridad
        try:
            subprocess.Popen([
                "notify-send",
                f"{icon_str} {title_text}",
                sub_text,
                "-u", "critical",
                "-i", AVATAR_FILE
            ])
        except Exception:
            pass

        # Maximizar ventana y traerla al frente absoluto
        self.set_resizable(True)
        self.deiconify()
        self.maximize()
        self.set_keep_above(True)
        self.present()
        self.queue_draw()

    def stop_ringing_audio(self):
        if self.ringing_process:
            try:
                self.ringing_process.terminate()
                self.ringing_process.wait(timeout=0.5)
            except Exception:
                try:
                    self.ringing_process.kill()
                except Exception:
                    pass
            self.ringing_process = None

    def stop_ringing(self):
        """Detiene la alarma, corta el audio y restaura la ventana a su tamaño normal flotante."""
        self.stop_ringing_audio()
        self.is_ringing = False
        self.nav_box.set_visible(True)
        self.set_keep_above(False)
        self.unmaximize()
        self.set_resizable(False)
        self.resize(390, 560)
        self.switch_tab(self.previous_tab)
        self.queue_draw()

    # =========================================================================
    # MÓDULO 1: TEMPORIZADOR (TIMER / POMODORO)
    # =========================================================================
    def build_timer_view(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(12)

        # Pantalla LCD
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.get_style_context().add_class("display-card")

        self.timer_label = Gtk.Label(label="05:00")
        self.timer_label.get_style_context().add_class("display-number")
        card.pack_start(self.timer_label, False, False, 0)

        # Barra de progreso
        self.timer_progress = Gtk.ProgressBar()
        self.timer_progress.set_fraction(1.0)
        card.pack_start(self.timer_progress, False, False, 4)

        self.timer_status = Gtk.Label(label="󰅐 Pomodoro & Cuenta Regresiva")
        self.timer_status.get_style_context().add_class("display-sub")
        card.pack_start(self.timer_status, False, False, 0)

        vbox.pack_start(card, False, False, 0)

        # Presets Rápidos
        p_label = Gtk.Label(label="Presets Rápidos:")
        p_label.set_xalign(0.0)
        p_label.get_style_context().add_class("display-sub")
        vbox.pack_start(p_label, False, False, 0)

        preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        presets = [("+5m", 300), ("+10m", 600), ("+15m", 900), ("+25m Pomodoro", 1500)]
        for lbl, secs in presets:
            btn = Gtk.Button(label=lbl)
            btn.get_style_context().add_class("preset-btn")
            btn.connect("clicked", lambda b, s=secs: self.add_timer_time(s))
            preset_box.pack_start(btn, True, True, 0)
        vbox.pack_start(preset_box, False, False, 0)

        # Ajustes Finos (+/-)
        fine_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        fines = [("+1m", 60), ("-1m", -60), ("+15s", 15), ("-15s", -15)]
        for lbl, secs in fines:
            btn = Gtk.Button(label=lbl)
            btn.get_style_context().add_class("header-btn")
            btn.connect("clicked", lambda b, s=secs: self.add_timer_time(s))
            fine_box.pack_start(btn, True, True, 0)
        vbox.pack_start(fine_box, False, False, 0)

        # Sesiones de Enfoque y Estudio
        study_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        study_presets = [("+30m", 1800), ("+45m", 2700), ("+50m", 3000), ("+60m", 3600)]
        for lbl, secs in study_presets:
            btn = Gtk.Button(label=lbl)
            btn.get_style_context().add_class("preset-btn")
            btn.connect("clicked", lambda b, s=secs: self.add_timer_time(s))
            study_box.pack_start(btn, True, True, 0)
        vbox.pack_start(study_box, False, False, 0)

        # Botones Principales de Control
        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.btn_timer_toggle = Gtk.Button(label="󰐊 Iniciar Temporizador")
        self.btn_timer_toggle.get_style_context().add_class("action-btn")
        self.btn_timer_toggle.get_style_context().add_class("action-btn-primary")
        self.btn_timer_toggle.connect("clicked", lambda b: self.toggle_timer())
        ctrl_box.pack_start(self.btn_timer_toggle, True, True, 0)

        self.btn_timer_reset = Gtk.Button(label="󰑓 Reiniciar")
        self.btn_timer_reset.get_style_context().add_class("action-btn")
        self.btn_timer_reset.get_style_context().add_class("action-btn-pink")
        self.btn_timer_reset.connect("clicked", lambda b: self.reset_timer())
        ctrl_box.pack_start(self.btn_timer_reset, True, True, 0)

        vbox.pack_start(ctrl_box, False, False, 4)

        # Tarjeta Informativa de Alerta
        timer_info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        timer_info.get_style_context().add_class("list-card")

        cur_snd_name = os.path.basename(self.config.get("alarm_sound_path", SOUND_ALARM_DEFAULT if os.path.exists(SOUND_ALARM_DEFAULT) else SOUND_HEAL))
        self.lbl_timer_sound = Gtk.Label(label=f"󰎆 Tono al finalizar: {cur_snd_name}")
        self.lbl_timer_sound.set_xalign(0.0)
        self.lbl_timer_sound.override_font(Pango.FontDescription("JetBrainsMono Nerd Font 10"))
        timer_info.pack_start(self.lbl_timer_sound, False, False, 0)

        hint_lbl = Gtk.Label(label="󰀠 Maximiza la ventana en grande con botón gigante para detener")
        hint_lbl.set_xalign(0.0)
        hint_lbl.get_style_context().add_class("display-sub")
        timer_info.pack_start(hint_lbl, False, False, 0)

        vbox.pack_start(timer_info, False, False, 0)

        self.stack.add_named(vbox, "tab_0")

    def update_timer_display(self):
        m = self.timer_seconds // 60
        s = self.timer_seconds % 60
        self.timer_label.set_text(f"{m:02d}:{s:02d}")
        frac = 0.0 if self.timer_initial <= 0 else max(0.0, min(1.0, self.timer_seconds / self.timer_initial))
        self.timer_progress.set_fraction(frac)

    def add_timer_time(self, secs):
        if not self.timer_running:
            self.timer_seconds = max(10, self.timer_seconds + secs)
            self.timer_initial = self.timer_seconds
        else:
            self.timer_seconds = max(5, self.timer_seconds + secs)
            self.timer_initial = max(self.timer_initial, self.timer_seconds)
        self.update_timer_display()

    def toggle_timer(self):
        if self.timer_running:
            self.timer_running = False
            self.btn_timer_toggle.set_label("󰐊 Reanudar")
            if self.timer_glib_id:
                GLib.source_remove(self.timer_glib_id)
                self.timer_glib_id = None
        else:
            if self.timer_seconds <= 0:
                self.timer_seconds = 300
                self.timer_initial = 300
            self.timer_running = True
            self.btn_timer_toggle.set_label("󰏤 Pausar")
            if self.config.get("sound", True):
                play_sound(SOUND_BLIP, volume=0.35)
            self.timer_glib_id = GLib.timeout_add_seconds(1, self.on_timer_tick)
        self.update_timer_display()

    def on_timer_tick(self):
        if not self.timer_running:
            return False

        self.timer_seconds -= 1
        self.update_timer_display()

        if self.timer_seconds <= 0:
            self.timer_running = False
            self.btn_timer_toggle.set_label("󰐊 Iniciar")
            self.timer_glib_id = None
            self.on_timer_finished()
            return False
        return True

    def reset_timer(self):
        self.timer_running = False
        if self.timer_glib_id:
            GLib.source_remove(self.timer_glib_id)
            self.timer_glib_id = None
        self.timer_seconds = self.timer_initial if self.timer_initial > 0 else 300
        self.btn_timer_toggle.set_label("󰐊 Iniciar")
        self.update_timer_display()

    def on_timer_finished(self):
        self.trigger_alarm_alert("¡TIEMPO CUMPLIDO!", "El temporizador de TimeDex ha finalizado.", icon_str="󰔛")

    # =========================================================================
    # MÓDULO 2: CRONÓMETRO (STOPWATCH CON VUELTAS / LAPS)
    # =========================================================================
    def build_chrono_view(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_border_width(12)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.get_style_context().add_class("display-card")

        self.chrono_label = Gtk.Label(label="00:00.00")
        self.chrono_label.get_style_context().add_class("display-number")
        card.pack_start(self.chrono_label, False, False, 0)

        sub_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.chrono_status = Gtk.Label(label="󰔚 Precisión a centésimas")
        self.chrono_status.get_style_context().add_class("display-sub")
        sub_box.pack_start(self.chrono_status, False, False, 0)

        spacer = Gtk.Box()
        sub_box.pack_start(spacer, True, True, 0)

        self.chrono_laps_count = Gtk.Label(label="0 Vueltas")
        self.chrono_laps_count.get_style_context().add_class("display-sub")
        sub_box.pack_start(self.chrono_laps_count, False, False, 0)

        card.pack_start(sub_box, False, False, 0)
        vbox.pack_start(card, False, False, 0)

        ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.btn_chrono_toggle = Gtk.Button(label="󰐊 Iniciar")
        self.btn_chrono_toggle.get_style_context().add_class("action-btn")
        self.btn_chrono_toggle.get_style_context().add_class("action-btn-primary")
        self.btn_chrono_toggle.connect("clicked", lambda b: self.toggle_chrono())
        ctrl_box.pack_start(self.btn_chrono_toggle, True, True, 0)

        self.btn_chrono_lap = Gtk.Button(label="󰑕 Vuelta")
        self.btn_chrono_lap.get_style_context().add_class("action-btn")
        self.btn_chrono_lap.connect("clicked", lambda b: self.add_chrono_lap())
        ctrl_box.pack_start(self.btn_chrono_lap, True, True, 0)

        self.btn_chrono_reset = Gtk.Button(label="󰑓 Reset")
        self.btn_chrono_reset.get_style_context().add_class("action-btn")
        self.btn_chrono_reset.get_style_context().add_class("action-btn-pink")
        self.btn_chrono_reset.connect("clicked", lambda b: self.reset_chrono())
        ctrl_box.pack_start(self.btn_chrono_reset, True, True, 0)

        vbox.pack_start(ctrl_box, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(220)

        self.laps_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.chrono_hint = Gtk.Label(label="󰔚 Presiona '󰑕 Vuelta' (o tecla L) para registrar tiempos parciales.")
        self.chrono_hint.get_style_context().add_class("display-sub")
        self.chrono_hint.set_padding(8, 20)
        self.laps_box.pack_start(self.chrono_hint, True, True, 0)

        scroll.add(self.laps_box)
        vbox.pack_start(scroll, True, True, 4)

        self.stack.add_named(vbox, "tab_1")

    def format_chrono(self, total_seconds):
        mins = int(total_seconds // 60)
        secs = int(total_seconds % 60)
        cents = int((total_seconds * 100) % 100)
        return f"{mins:02d}:{secs:02d}.{cents:02d}"

    def toggle_chrono(self):
        if self.chrono_running:
            self.chrono_running = False
            self.chrono_elapsed += time.time() - self.chrono_start_time
            self.btn_chrono_toggle.set_label("󰐊 Reanudar")
            if self.chrono_glib_id:
                GLib.source_remove(self.chrono_glib_id)
                self.chrono_glib_id = None
        else:
            self.chrono_running = True
            self.chrono_start_time = time.time()
            self.btn_chrono_toggle.set_label("󰏤 Pausar")
            if self.config.get("sound", True):
                play_sound(SOUND_BLIP, volume=0.3)
            self.chrono_glib_id = GLib.timeout_add(30, self.on_chrono_tick)

    def on_chrono_tick(self):
        if not self.chrono_running:
            return False
        cur = self.chrono_elapsed + (time.time() - self.chrono_start_time)
        self.chrono_label.set_text(self.format_chrono(cur))
        return True

    def add_chrono_lap(self):
        if not self.chrono_running and self.chrono_elapsed == 0:
            return

        if hasattr(self, 'chrono_hint') and self.chrono_hint in self.laps_box.get_children():
            self.laps_box.remove(self.chrono_hint)

        cur = self.chrono_elapsed + (time.time() - self.chrono_start_time if self.chrono_running else 0)
        lap_num = len(self.chrono_laps) + 1
        prev_total = self.chrono_laps[-1]["total"] if self.chrono_laps else 0.0
        lap_delta = cur - prev_total

        self.chrono_laps.append({"num": lap_num, "delta": lap_delta, "total": cur})
        self.chrono_laps_count.set_text(f"{lap_num} Vueltas")

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.get_style_context().add_class("list-card")

        lbl_num = Gtk.Label(label=f"Vuelta #{lap_num:02d}")
        lbl_num.get_style_context().add_class("display-sub")
        row.pack_start(lbl_num, False, False, 0)

        spacer = Gtk.Box()
        row.pack_start(spacer, True, True, 0)

        lbl_delta = Gtk.Label(label=f"+{self.format_chrono(lap_delta)}")
        lbl_delta.override_font(Pango.FontDescription("JetBrainsMono Nerd Font Bold 11"))
        row.pack_start(lbl_delta, False, False, 6)

        lbl_tot = Gtk.Label(label=self.format_chrono(cur))
        lbl_tot.override_font(Pango.FontDescription("JetBrainsMono Nerd Font 11"))
        row.pack_start(lbl_tot, False, False, 0)

        self.laps_box.pack_start(row, False, False, 0)
        self.laps_box.reorder_child(row, 0)
        self.laps_box.show_all()

        if self.config.get("sound", True):
            play_sound(SOUND_BLIP, volume=0.25)

    def reset_chrono(self):
        self.chrono_running = False
        if self.chrono_glib_id:
            GLib.source_remove(self.chrono_glib_id)
            self.chrono_glib_id = None
        self.chrono_elapsed = 0.0
        self.chrono_start_time = 0.0
        self.chrono_laps = []
        self.chrono_label.set_text("00:00.00")
        self.chrono_laps_count.set_text("0 Vueltas")
        self.btn_chrono_toggle.set_label("󰐊 Iniciar")

        for child in self.laps_box.get_children():
            self.laps_box.remove(child)
        if hasattr(self, 'chrono_hint'):
            self.laps_box.pack_start(self.chrono_hint, True, True, 0)
        self.laps_box.show_all()

    # =========================================================================
    # MÓDULO 3: ALARMAS PERSISTENTES & CONFIGURACIÓN DE AUDIO
    # =========================================================================
    def build_alarms_view(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_border_width(12)

        # Creador de Nueva Alarma
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        card.get_style_context().add_class("display-card")

        head_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon_lbl = Gtk.Label(label="󰀠")
        icon_lbl.override_font(Pango.FontDescription("JetBrainsMono Nerd Font 13"))
        head_box.pack_start(icon_lbl, False, False, 0)
        title = Gtk.Label(label="Programar Alarma")
        title.override_font(Pango.FontDescription("Inter Bold 12"))
        head_box.pack_start(title, False, False, 0)
        card.pack_start(head_box, False, False, 0)

        inp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        now = datetime.datetime.now()
        self.spin_hour = Gtk.SpinButton.new_with_range(0, 23, 1)
        self.spin_hour.set_value(now.hour)
        inp_box.pack_start(self.spin_hour, False, False, 0)

        sep = Gtk.Label(label=":")
        sep.override_font(Pango.FontDescription("Press Start 2P 14"))
        inp_box.pack_start(sep, False, False, 0)

        self.spin_min = Gtk.SpinButton.new_with_range(0, 59, 1)
        # Por defecto +1 minuto del actual para test inmediato
        self.spin_min.set_value((now.minute + 1) % 60)
        inp_box.pack_start(self.spin_min, False, False, 0)

        self.entry_alarm_tag = Gtk.Entry()
        self.entry_alarm_tag.set_placeholder_text("Etiqueta (ej. Descanso)")
        inp_box.pack_start(self.entry_alarm_tag, True, True, 0)

        card.pack_start(inp_box, False, False, 0)

        btn_add = Gtk.Button(label="󰐕 Añadir y Activar Alarma")
        btn_add.get_style_context().add_class("action-btn")
        btn_add.get_style_context().add_class("action-btn-primary")
        btn_add.connect("clicked", lambda b: self.add_new_alarm())
        card.pack_start(btn_add, False, False, 2)

        vbox.pack_start(card, False, False, 0)

        # Selector de Sonido Personalizado (MP3 / WAV)
        sound_card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        sound_card.get_style_context().add_class("list-card")

        cur_sound = self.config.get("alarm_sound_path", SOUND_ALARM_DEFAULT if os.path.exists(SOUND_ALARM_DEFAULT) else SOUND_HEAL)
        sound_basename = os.path.basename(cur_sound)
        self.lbl_sound_name = Gtk.Label(label=f"󰎆 Tono: {sound_basename}")
        self.lbl_sound_name.override_font(Pango.FontDescription("JetBrainsMono Nerd Font 10"))
        sound_card.pack_start(self.lbl_sound_name, False, False, 0)

        sp = Gtk.Box()
        sound_card.pack_start(sp, True, True, 0)

        btn_pick_sound = Gtk.Button(label="Elegir MP3")
        btn_pick_sound.get_style_context().add_class("header-btn")
        btn_pick_sound.connect("clicked", lambda b: self.choose_alarm_sound())
        sound_card.pack_start(btn_pick_sound, False, False, 0)

        btn_test_sound = Gtk.Button(label="Probar")
        btn_test_sound.get_style_context().add_class("header-btn")
        btn_test_sound.connect("clicked", lambda b: self.preview_alarm_sound())
        sound_card.pack_start(btn_test_sound, False, False, 0)

        vbox.pack_start(sound_card, False, False, 0)

        # Lista de Alarmas Guardadas
        list_label = Gtk.Label(label="Alarmas Registradas:")
        list_label.set_xalign(0.0)
        list_label.get_style_context().add_class("display-sub")
        vbox.pack_start(list_label, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(140)

        self.alarms_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        scroll.add(self.alarms_list_box)
        vbox.pack_start(scroll, True, True, 0)

        self.render_alarms_list()
        self.stack.add_named(vbox, "tab_2")

    def choose_alarm_sound(self):
        """Abre un diálogo nativo para seleccionar cualquier archivo MP3 o WAV de alarma."""
        dialog = Gtk.FileChooserNative.new(
            "Seleccionar tono de alarma (MP3 o WAV)",
            self,
            Gtk.FileChooserAction.OPEN,
            "Seleccionar",
            "Cancelar"
        )
        filter_audio = Gtk.FileFilter()
        filter_audio.set_name("Archivos de Audio (*.mp3, *.wav, *.ogg, *.flac)")
        filter_audio.add_mime_type("audio/*")
        filter_audio.add_pattern("*.mp3")
        filter_audio.add_pattern("*.wav")
        filter_audio.add_pattern("*.ogg")
        filter_audio.add_pattern("*.flac")
        dialog.add_filter(filter_audio)

        # Iniciar en Descargas o carpeta de sonidos
        downloads_dir = os.path.join(HOME, "Descargas")
        if os.path.exists(downloads_dir):
            dialog.set_current_folder(downloads_dir)

        response = dialog.run()
        if response == Gtk.ResponseType.ACCEPT:
            filename = dialog.get_filename()
            if filename:
                self.config["alarm_sound_path"] = filename
                save_config(self.config)
                self.lbl_sound_name.set_text(f"󰎆 Tono: {os.path.basename(filename)}")
                # Probar 2 segundos
                self.preview_alarm_sound()
        dialog.destroy()

    def preview_alarm_sound(self):
        snd = self.config.get("alarm_sound_path", SOUND_ALARM_DEFAULT if os.path.exists(SOUND_ALARM_DEFAULT) else SOUND_HEAL)
        if snd and os.path.exists(snd):
            proc = start_alarm_audio_loop(snd)
            if proc:
                GLib.timeout_add(2500, lambda: proc.terminate() or False)

    def render_alarms_list(self):
        for c in self.alarms_list_box.get_children():
            self.alarms_list_box.remove(c)

        if not self.alarms:
            empty = Gtk.Label(label="No hay alarmas configuradas.\nAjusta la hora arriba y presiona 'Añadir y Activar Alarma'.")
            empty.set_justify(Gtk.Justification.CENTER)
            empty.get_style_context().add_class("display-sub")
            empty.set_padding(0, 16)
            self.alarms_list_box.pack_start(empty, False, False, 0)
        else:
            for idx, item in enumerate(self.alarms):
                row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                row.get_style_context().add_class("list-card")

                lbl_time = Gtk.Label(label=f"{item['hour']:02d}:{item['minute']:02d}")
                lbl_time.override_font(Pango.FontDescription("Press Start 2P 13"))
                row.pack_start(lbl_time, False, False, 0)

                lbl_tag = Gtk.Label(label=item.get("tag", "Alarma"))
                lbl_tag.override_font(Pango.FontDescription("Inter Bold 11"))
                row.pack_start(lbl_tag, False, False, 6)

                spacer = Gtk.Box()
                row.pack_start(spacer, True, True, 0)

                sw = Gtk.Switch()
                sw.set_active(item.get("active", True))
                sw.connect("state-set", lambda s, state, i=idx: self.toggle_alarm_state(i, state))
                row.pack_start(sw, False, False, 4)

                btn_del = Gtk.Button(label="󰅖")
                btn_del.get_style_context().add_class("header-btn")
                btn_del.get_style_context().add_class("header-btn-close")
                btn_del.connect("clicked", lambda b, i=idx: self.delete_alarm(i))
                row.pack_start(btn_del, False, False, 0)

                self.alarms_list_box.pack_start(row, False, False, 0)

        self.alarms_list_box.show_all()

    def add_new_alarm(self):
        h = int(self.spin_hour.get_value())
        m = int(self.spin_min.get_value())
        tag = self.entry_alarm_tag.get_text().strip() or "Alarma"

        self.alarms.append({
            "hour": h,
            "minute": m,
            "tag": tag,
            "active": True
        })
        save_alarms(self.alarms)
        self.entry_alarm_tag.set_text("")
        self.render_alarms_list()
        if self.config.get("sound", True):
            play_sound(SOUND_BLIP, volume=0.35)

    def toggle_alarm_state(self, idx, state):
        if 0 <= idx < len(self.alarms):
            self.alarms[idx]["active"] = state
            save_alarms(self.alarms)
        return False

    def delete_alarm(self, idx):
        if 0 <= idx < len(self.alarms):
            self.alarms.pop(idx)
            save_alarms(self.alarms)
            self.render_alarms_list()

    def check_alarms(self, now):
        """Verificación precisa cada segundo que no ignora alarmas creadas en el minuto actual."""
        cur_min_key = now.strftime("%Y-%m-%d %H:%M")
        if self.last_check_minute != cur_min_key:
            self.last_check_minute = cur_min_key
            self.fired_alarm_keys.clear()

        for idx, item in enumerate(self.alarms):
            if item.get("active", True):
                if item["hour"] == now.hour and item["minute"] == now.minute:
                    alarm_key = f"{item['hour']}:{item['minute']}:{item.get('tag', '')}:{idx}"
                    if alarm_key not in self.fired_alarm_keys:
                        self.fired_alarm_keys.add(alarm_key)
                        self.fire_alarm(item)

    def fire_alarm(self, item):
        tag = item.get("tag", "Alarma")
        time_str = f"{item['hour']:02d}:{item['minute']:02d}"
        self.trigger_alarm_alert(f"¡ALARMA: {time_str}!", tag, icon_str="󰀠")

    # =========================================================================
    # MÓDULO 4: RELOJ DIGITAL & HORAS MUNDIALES (100% OFFLINE IANA)
    # =========================================================================
    def build_clock_view(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_border_width(12)

        # 1. Reloj Principal Digital HUD (Hora Local)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card.get_style_context().add_class("display-card")

        self.clock_time_label = Gtk.Label(label="--:--:--")
        self.clock_time_label.get_style_context().add_class("display-number")
        self.clock_time_label.override_font(Pango.FontDescription("Press Start 2P 24"))
        card.pack_start(self.clock_time_label, False, False, 2)

        self.clock_date_label = Gtk.Label(label="Cargando fecha...")
        self.clock_date_label.override_font(Pango.FontDescription("Inter Bold 13"))
        self.clock_date_label.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 0.95))
        card.pack_start(self.clock_date_label, False, False, 2)

        tz_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        tz_box.set_halign(Gtk.Align.CENTER)
        icon_local = Gtk.Label(label="󰥔")
        icon_local.override_font(Pango.FontDescription("JetBrainsMono Nerd Font 12"))
        icon_local.get_style_context().add_class("display-sub")
        tz_box.pack_start(icon_local, False, False, 0)
        self.clock_tz_label = Gtk.Label(label="Zona Local: calculando...")
        self.clock_tz_label.get_style_context().add_class("display-sub")
        tz_box.pack_start(self.clock_tz_label, False, False, 0)
        card.pack_start(tz_box, False, False, 2)

        # Fila de Clima en Vivo (Open-Meteo)
        self.weather_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.weather_box.set_halign(Gtk.Align.CENTER)

        self.icon_weather = Gtk.Label(label="󰖕")
        self.icon_weather.override_font(Pango.FontDescription("JetBrainsMono Nerd Font 11"))
        self.icon_weather.get_style_context().add_class("display-sub")
        self.weather_box.pack_start(self.icon_weather, False, False, 0)

        self.lbl_weather = Gtk.Label(label="Sincronizando clima...")
        self.lbl_weather.override_font(Pango.FontDescription("Inter 10"))
        self.lbl_weather.get_style_context().add_class("display-sub")
        self.weather_box.pack_start(self.lbl_weather, False, False, 0)
        card.pack_start(self.weather_box, False, False, 2)

        vbox.pack_start(card, False, False, 0)

        # 2. Selector para Agregar Horas Internacionales
        add_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        add_box.get_style_context().add_class("list-card")

        self.combo_world_tz = Gtk.ComboBoxText.new_with_entry()
        self.combo_world_tz.set_hexpand(True)
        entry_child = self.combo_world_tz.get_child()
        if isinstance(entry_child, Gtk.Entry):
            entry_child.set_placeholder_text("Selecciona o escribe ciudad/zona...")

        for tz_id, label_city in PRESET_CITIES:
            self.combo_world_tz.append(tz_id, label_city)

        self.combo_world_tz.set_active(0)
        add_box.pack_start(self.combo_world_tz, True, True, 0)

        btn_add_tz = Gtk.Button(label="󰐕 Añadir")
        btn_add_tz.get_style_context().add_class("action-btn")
        btn_add_tz.get_style_context().add_class("action-btn-primary")
        btn_add_tz.connect("clicked", lambda b: self.add_world_clock())
        add_box.pack_start(btn_add_tz, False, False, 0)

        vbox.pack_start(add_box, False, False, 0)

        # 3. Lista de Relojes Mundiales en ScrolledWindow
        header_world = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon_world = Gtk.Label(label="󰥔")
        icon_world.override_font(Pango.FontDescription("JetBrainsMono Nerd Font 13"))
        header_world.pack_start(icon_world, False, False, 0)

        lbl_world_title = Gtk.Label(label="Horas Internacionales:")
        lbl_world_title.override_font(Pango.FontDescription("Inter Bold 11"))
        lbl_world_title.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 0.9))
        header_world.pack_start(lbl_world_title, False, False, 0)

        sp = Gtk.Box()
        header_world.pack_start(sp, True, True, 0)

        lbl_offline = Gtk.Label(label="󰄬 100% Offline (tzdata IANA)")
        lbl_offline.get_style_context().add_class("display-sub")
        header_world.pack_start(lbl_offline, False, False, 0)

        vbox.pack_start(header_world, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(165)

        self.world_clocks_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        scroll.add(self.world_clocks_box)
        vbox.pack_start(scroll, True, True, 0)

        self.stack.add_named(vbox, "tab_3")
        self.world_clock_widgets = []
        self.rebuild_world_clocks_ui()
        self.update_weather_display()
        self.update_clock()

    def rebuild_world_clocks_ui(self):
        for child in self.world_clocks_box.get_children():
            self.world_clocks_box.remove(child)
        self.world_clock_widgets = []

        if not self.world_clocks:
            card_empty = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            card_empty.get_style_context().add_class("list-card")
            lbl_empty = Gtk.Label(label="󰥔  No hay países agregados.\nSelecciona una ciudad arriba y pulsa '󰐕 Añadir'.")
            lbl_empty.get_style_context().add_class("display-sub")
            lbl_empty.set_justify(Gtk.Justification.CENTER)
            lbl_empty.set_padding(12, 16)
            card_empty.pack_start(lbl_empty, True, True, 0)
            self.world_clocks_box.pack_start(card_empty, False, False, 0)
            self.world_clocks_box.show_all()
            return

        for idx, item in enumerate(self.world_clocks):
            card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            card.get_style_context().add_class("list-card")

            # Left side: City name + relative difference
            left_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)

            title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            icon_city = Gtk.Label(label="󰥔")
            icon_city.override_font(Pango.FontDescription("JetBrainsMono Nerd Font 12"))
            title_row.pack_start(icon_city, False, False, 0)

            lbl_name = Gtk.Label(label=item['name'])
            lbl_name.set_xalign(0.0)
            lbl_name.override_font(Pango.FontDescription("Inter Bold 11"))
            lbl_name.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 0.95))
            title_row.pack_start(lbl_name, False, False, 0)
            left_box.pack_start(title_row, False, False, 0)

            lbl_diff = Gtk.Label(label="Calculando...")
            lbl_diff.set_xalign(0.0)
            lbl_diff.get_style_context().add_class("display-sub")
            left_box.pack_start(lbl_diff, False, False, 0)

            card.pack_start(left_box, True, True, 0)

            # Right side: Digital time + Remove button
            right_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            lbl_time = Gtk.Label(label="--:--:--")
            lbl_time.override_font(Pango.FontDescription("JetBrainsMono Nerd Font Bold 13"))
            lbl_time.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1, 1, 1, 1.0))
            right_box.pack_start(lbl_time, False, False, 0)

            btn_del = Gtk.Button(label="󰅖")
            btn_del.get_style_context().add_class("header-btn")
            btn_del.set_tooltip_text(f"Eliminar {item['name']}")
            btn_del.connect("clicked", lambda b, i=idx: self.remove_world_clock(i))
            right_box.pack_start(btn_del, False, False, 0)

            card.pack_start(right_box, False, False, 0)
            self.world_clocks_box.pack_start(card, False, False, 0)

            self.world_clock_widgets.append({
                "time_label": lbl_time,
                "diff_label": lbl_diff,
                "tz": item["tz"]
            })

        self.world_clocks_box.show_all()

    def add_world_clock(self):
        tz_id = self.combo_world_tz.get_active_id()
        active_text = self.combo_world_tz.get_active_text()

        if not active_text:
            return

        tz_str = tz_id if tz_id else active_text.strip()
        try:
            zoneinfo.ZoneInfo(tz_str)
            name = active_text.strip()
            if not tz_id:
                name = tz_str.split("/")[-1].replace("_", " ")
        except Exception:
            return

        for existing in self.world_clocks:
            if existing.get("tz") == tz_str:
                return

        play_sound(SOUND_BLIP)
        self.world_clocks.append({"name": name, "tz": tz_str})
        self.config["world_clocks"] = self.world_clocks
        save_config(self.config)
        self.rebuild_world_clocks_ui()
        self.update_clock()

    def remove_world_clock(self, idx):
        if 0 <= idx < len(self.world_clocks):
            play_sound(SOUND_BLIP)
            self.world_clocks.pop(idx)
            self.config["world_clocks"] = self.world_clocks
            save_config(self.config)
            self.rebuild_world_clocks_ui()
            self.update_clock()

    def update_clock(self):
        now_local = datetime.datetime.now().astimezone()
        self.clock_time_label.set_text(now_local.strftime("%H:%M:%S"))

        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        dia_sem = dias[now_local.weekday()]
        mes = meses[now_local.month - 1]
        self.clock_date_label.set_text(f"{dia_sem}, {now_local.day} de {mes} de {now_local.year}")

        # Zona Horaria Local y semana
        local_tz_name = now_local.tzname() or "Local"
        week_num = now_local.isocalendar()[1]
        offset_sec = now_local.utcoffset().total_seconds()
        offset_hours = int(offset_sec // 3600)
        gmt_str = f"GMT{offset_hours:+d}"
        self.clock_tz_label.set_text(f"Zona Local: {local_tz_name} ({gmt_str}) • Semana {week_num}")

        # Actualizar Relojes Mundiales (100% Offline con zoneinfo)
        for item in self.world_clock_widgets:
            try:
                tz = zoneinfo.ZoneInfo(item["tz"])
                now_target = datetime.datetime.now(tz)
                item["time_label"].set_text(now_target.strftime("%H:%M:%S"))

                diff_sec = (now_target.utcoffset() - now_local.utcoffset()).total_seconds()
                diff_h = int(diff_sec // 3600)
                diff_m = int((abs(diff_sec) % 3600) // 60)
                sign = "+" if diff_sec >= 0 else ""
                diff_str = f"{sign}{diff_h}h" if diff_m == 0 else f"{sign}{diff_h}h {diff_m}m"

                if now_target.date() > now_local.date():
                    day_str = "Mañana"
                elif now_target.date() < now_local.date():
                    day_str = "Ayer"
                else:
                    day_str = "Hoy"

                tz_abbr = now_target.tzname() or item["tz"].split("/")[-1]
                item["diff_label"].set_text(f"{diff_str} • {day_str} • {tz_abbr}")
            except Exception:
                pass

    def update_weather_display(self):
        cache_file = os.path.expanduser("~/.cache/gardevoir-weather/weather.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cdata = json.load(f)
                    w = cdata.get("data", {})
                    icon = w.get("icon", "󰖕")
                    temp = w.get("temperature", 22)
                    desc = w.get("description", "Clima")
                    feels = w.get("apparent_temperature", temp)
                    hum = w.get("humidity", 50)
                    city = w.get("city", "")

                    if hasattr(self, 'icon_weather'):
                        self.icon_weather.set_text(icon)
                    if hasattr(self, 'lbl_weather'):
                        city_str = f" • {city}" if city else ""
                        self.lbl_weather.set_text(f"{temp}°C  {desc} • Sensación {feels}°C • Humedad {hum}%{city_str}")
                    return
            except Exception:
                pass
        if hasattr(self, 'lbl_weather'):
            self.lbl_weather.set_text("Clima sincronizando...")

    def refresh_weather_tick(self):
        try:
            weather_bin = os.path.expanduser("~/.local/bin/gardevoir-weather.py")
            if os.path.exists(weather_bin):
                subprocess.Popen([weather_bin, "icon"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
        self.update_weather_display()
        return True

    def on_clock_tick(self):
        now = datetime.datetime.now()
        self.update_clock()
        self.check_alarms(now)
        return True

    # =========================================================================
    # EVENTOS DE TECLADO
    # =========================================================================
    def on_key_press(self, widget, event):
        keyval = event.keyval
        keyname = Gdk.keyval_name(keyval)
        state = event.state

        # Si la alarma está timbrando, cualquier tecla principal la detiene
        if self.is_ringing:
            if keyname in ['space', 'Return', 'KP_Enter', 'Escape']:
                self.stop_ringing()
                return True

        # Ctrl + Q: Salir
        if (state & Gdk.ModifierType.CONTROL_MASK) and keyname in ['q', 'Q']:
            self.stop_ringing_audio()
            self.destroy()
            return True

        # Escape: Cerrar aplicación (como pidió el usuario)
        if keyname == 'Escape':
            self.stop_ringing_audio()
            self.destroy()
            return True

        # Cambio de Pestañas: 1, 2, 3, 4
        if keyname in ['1', 'KP_1']:
            self.switch_tab(0)
            return True
        elif keyname in ['2', 'KP_2']:
            self.switch_tab(1)
            return True
        elif keyname in ['3', 'KP_3']:
            self.switch_tab(2)
            return True
        elif keyname in ['4', 'KP_4']:
            self.switch_tab(3)
            return True

        # Espacio: Iniciar/Pausa en la pestaña activa
        if keyname == 'space':
            cur = self.stack.get_visible_child_name()
            if cur == "tab_0":
                self.toggle_timer()
                return True
            elif cur == "tab_1":
                self.toggle_chrono()
                return True

        # Tecla R: Reset
        if keyname in ['r', 'R'] and not (state & Gdk.ModifierType.CONTROL_MASK):
            cur = self.stack.get_visible_child_name()
            if cur == "tab_0":
                self.reset_timer()
                return True
            elif cur == "tab_1":
                self.reset_chrono()
                return True

        # Tecla L: Lap en cronómetro
        if keyname in ['l', 'L'] and not (state & Gdk.ModifierType.CONTROL_MASK):
            if self.stack.get_visible_child_name() == "tab_1":
                self.add_chrono_lap()
                return True

        # Tecla S: Sonido
        if keyname in ['s', 'S'] and not (state & Gdk.ModifierType.CONTROL_MASK):
            self.toggle_sound()
            return True

        return False


def main():
    app = GardevoirTimeDex()
    app.connect("destroy", lambda w: (app.stop_ringing_audio(), Gtk.main_quit()))
    app.show_all()
    # Abrir y seleccionar Reloj (pestaña 3) al iniciar
    app.switch_tab(3)
    app.present()
    Gtk.main()


if __name__ == "__main__":
    main()
