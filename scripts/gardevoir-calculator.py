#!/usr/bin/env python3
"""
🌸 Gardevoir Poké-Calc - Calculadora Estilo Glassmorphism & Pokémon
Adaptada a Arch Linux + Cinnamon.
Integrada con dynamic-theme.py, fuentes retro 'Press Start 2P',
efectos de sonido Pokémon y soporte completo de teclado.
"""

import os
import sys
import math
import re
import json
import time
import subprocess
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib, Pango
import cairo

HOME = str(Path.home())
CONFIG_DIR = os.path.join(HOME, ".config/gardevoir-calc")
THEME_JSON = os.path.join(CONFIG_DIR, "theme.json")
CONFIG_JSON = os.path.join(CONFIG_DIR, "config.json")
SOUND_FILE = os.path.join(HOME, ".local/share/sounds/pokemon/pokeball_blip.wav")
AVATAR_FILE = os.path.join(HOME, ".local/share/gardevoir-greeter/avatar.png")
SOCKET_FILE = f"/tmp/gardevoir_calc_{os.getuid()}.sock"


def play_sound(sound_path=SOUND_FILE, volume=0.35):
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
    """Carga colores del tema dinámico o usa los valores por defecto de Gardevoir."""
    defaults = {
        "dom_hex": "#141228",
        "accent_hex": "#4f33c7",
        "accent_dim_hex": "#271a63",
        "horn_pink": "#FF4370",
        "text_white": "#FFFFFF",
        "text_muted": "#CBD5E1"
    }
    if os.path.exists(THEME_JSON):
        try:
            with open(THEME_JSON, "r") as f:
                data = json.load(f)
                defaults.update(data)
        except Exception:
            pass
    return defaults


def load_config():
    """Carga configuración del usuario (sonido, DEG/RAD)."""
    defaults = {
        "sound": True,
        "angle_mode": "DEG"
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


class GardevoirCalculator(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("Gardevoir Poké-Calc")
        self.set_wmclass("gardevoir-calc", "GardevoirCalc")
        self.set_role("gardevoir-calculator")
        self.set_default_size(360, 520)
        self.set_resizable(False)
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_position(Gtk.WindowPosition.CENTER)

        # Configuración RGBA para bordes curvos y transparencia glass limpia
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)

        self.connect("draw", self.on_draw)

        # Estado
        self.config = load_config()
        self.theme = load_theme()
        self.current_expr = ""
        self.last_result = "0"
        self.ans = 0.0
        self.just_calculated = False
        self.last_theme_mtime = os.path.getmtime(THEME_JSON) if os.path.exists(THEME_JSON) else 0

        # Proveedor de CSS
        self.css_provider = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(
            screen, self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.apply_theme()

        # Construir Interfaz
        self.build_ui()

        # Eventos de teclado
        self.connect("key-press-event", self.on_key_press)

        # Monitorear cambios de tema (para actualizar al cambiar de fondo con Win + G)
        GLib.timeout_add(1000, self.check_theme_update)

        if self.config.get("sound", True):
            play_sound(SOUND_FILE, volume=0.35)

    def on_draw(self, widget, cr):
        alloc = widget.get_allocation()
        w, h = alloc.width, alloc.height

        # 1. Limpiar canvas con transparencia completa para esquinas redondeadas
        cr.set_source_rgba(0, 0, 0, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        # 2. Trazar rectángulo redondeado
        cr.set_operator(cairo.OPERATOR_OVER)
        radius = 16.0
        degrees = math.pi / 180.0

        cr.new_sub_path()
        cr.arc(w - radius, radius, radius, -90 * degrees, 0 * degrees)
        cr.arc(w - radius, h - radius, radius, 0 * degrees, 90 * degrees)
        cr.arc(radius, h - radius, radius, 90 * degrees, 180 * degrees)
        cr.arc(radius, radius, radius, 180 * degrees, 270 * degrees)
        cr.close_path()

        # 3. Cristal Ahumado (Obsidian Smoked Glass)
        # Atenúa un 88% cualquier ventana o texto de fondo manteniendo el look glass translúcido
        t = self.theme
        dr, dg, db = hex_to_rgb(t["dom_hex"])
        # Tonalidad oscura profunda derivada del fondo
        bg_r = max(0.03, (dr / 255.0) * 0.6)
        bg_g = max(0.04, (dg / 255.0) * 0.6)
        bg_b = max(0.08, (db / 255.0) * 0.7)
        cr.set_source_rgba(bg_r, bg_g, bg_b, 0.88)
        cr.fill_preserve()

        # 4. Borde Neón Dinámico
        ar, ag, ab = hex_to_rgb(t["accent_hex"])
        cr.set_source_rgba(ar / 255.0, ag / 255.0, ab / 255.0, 0.95)
        cr.set_line_width(1.5)
        cr.stroke()

        return False

    def apply_theme(self):
        t = self.theme
        dr, dg, db = hex_to_rgb(t["dom_hex"])
        ar, ag, ab = hex_to_rgb(t["accent_hex"])
        accent = t["accent_hex"]
        dim = t["accent_dim_hex"]
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
            box-shadow: 0 0 10px {accent};
            color: #FFFFFF;
            outline: none;
        }}
        .header-btn-close:focus,
        .header-btn-close:hover {{
            background-color: {pink};
            border-color: {pink};
            box-shadow: 0 0 12px {pink};
            color: #FFFFFF;
            outline: none;
        }}

        .display-box {{
            background-color: rgba(4, 6, 12, 0.88);
            border: 1px solid rgba({ar}, {ag}, {ab}, 0.50);
            border-radius: 12px;
            margin: 12px 14px 8px 14px;
            padding: 10px 14px;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.5);
        }}

        .history-label {{
            font-family: 'JetBrainsMono Nerd Font', monospace;
            font-size: 12px;
            color: #94A3B8;
        }}

        .result-label {{
            font-family: 'Press Start 2P', monospace;
            font-size: 18px;
            color: #FFFFFF;
            text-shadow: 0 0 10px {accent}, 0 0 20px {accent};
            padding-top: 6px;
            padding-bottom: 4px;
        }}

        .status-badge {{
            font-family: 'JetBrainsMono Nerd Font', monospace;
            font-size: 10px;
            color: #CBD5E1;
        }}
        .status-badge-accent {{
            color: {pink};
            font-weight: bold;
        }}

        .calc-grid {{
            padding: 6px 14px 14px 14px;
        }}

        /* Botones Base (Números en Blanco Puro) */
        .calc-btn {{
            font-family: 'JetBrainsMono Nerd Font', 'Inter', monospace;
            font-size: 15px;
            font-weight: 800;
            color: #FFFFFF;
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 9px;
            min-height: 42px;
            min-width: 52px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
            transition: all 100ms ease;
        }}
        .calc-btn:focus,
        .calc-btn:hover {{
            background-color: rgba({ar}, {ag}, {ab}, 0.32);
            border-color: {accent};
            box-shadow: 0 0 14px {accent}, inset 0 0 6px rgba({ar}, {ag}, {ab}, 0.4);
            outline: none;
        }}
        .calc-btn:active {{
            background-color: rgba({ar}, {ag}, {ab}, 0.50);
        }}

        /* Operadores (+ - × ÷ ^) -> Acento dinámico */
        .calc-btn-op {{
            color: {accent};
            font-size: 16px;
            background-color: rgba({ar}, {ag}, {ab}, 0.12);
            border-color: rgba({ar}, {ag}, {ab}, 0.30);
        }}
        .calc-btn-op:hover {{
            background-color: rgba({ar}, {ag}, {ab}, 0.28);
            border-color: {accent};
            color: #FFFFFF;
        }}

        /* Funciones (sin cos tan ln % Ans) -> Lila psíquico */
        .calc-btn-fn {{
            font-size: 12px;
            font-weight: 700;
            color: #c084fc;
            background-color: rgba(192, 132, 252, 0.08);
            border-color: rgba(192, 132, 252, 0.25);
        }}
        .calc-btn-fn:hover {{
            background-color: rgba(192, 132, 252, 0.25);
            border-color: #c084fc;
            color: #FFFFFF;
        }}

        /* Botón Clear (C) -> Rosa Gardevoir */
        .calc-btn-clear {{
            color: #FFFFFF;
            background-color: rgba(255, 67, 112, 0.35);
            border-color: {pink};
            font-weight: 800;
        }}
        .calc-btn-clear:hover {{
            background-color: {pink};
            border-color: {pink};
            box-shadow: 0 0 12px {pink};
            color: #FFFFFF;
        }}

        /* Botón Igual (=) -> Neón de Acento Dinámico */
        .calc-btn-eq {{
            color: #FFFFFF;
            background-color: {accent};
            border-color: {accent};
            font-size: 18px;
            font-weight: 800;
            box-shadow: 0 0 14px rgba({ar}, {ag}, {ab}, 0.6);
        }}
        .calc-btn-eq:hover {{
            background-color: {accent};
            box-shadow: 0 0 20px {accent};
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
        return True

    def build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.get_style_context().add_class("calc-root")
        self.add(main_box)

        # 1. Barra de Encabezado Personalizada
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

        # Título
        title_label = Gtk.Label(label="GARDEVOIR POKÉ-CALC")
        title_label.get_style_context().add_class("calc-title")
        h_box.pack_start(title_label, False, False, 0)

        # Espaciador
        spacer = Gtk.Box()
        h_box.pack_start(spacer, True, True, 0)

        # Botones de Control
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        # Botón DEG/RAD
        self.angle_btn = Gtk.Button(label=self.config.get("angle_mode", "DEG"))
        self.angle_btn.get_style_context().add_class("header-btn")
        self.angle_btn.set_tooltip_text("Alternar entre Grados (DEG) y Radianes (RAD) [Tecla D]")
        self.angle_btn.connect("clicked", self.toggle_angle_mode)
        btn_box.pack_start(self.angle_btn, False, False, 0)

        # Botón Sonido
        snd_label = "󰕾" if self.config.get("sound", True) else "󰝟"
        self.sound_btn = Gtk.Button(label=snd_label)
        self.sound_btn.get_style_context().add_class("header-btn")
        self.sound_btn.set_tooltip_text("Activar/Desactivar sonido Pokémon [Tecla S]")
        self.sound_btn.connect("clicked", self.toggle_sound)
        btn_box.pack_start(self.sound_btn, False, False, 0)

        # Botón Minimizar
        min_btn = Gtk.Button(label="󰍵")
        min_btn.get_style_context().add_class("header-btn")
        min_btn.set_tooltip_text("Minimizar")
        min_btn.connect("clicked", lambda b: self.iconify())
        btn_box.pack_start(min_btn, False, False, 0)

        # Botón Cerrar
        close_btn = Gtk.Button(label="󰅖")
        close_btn.get_style_context().add_class("header-btn")
        close_btn.get_style_context().add_class("header-btn-close")
        close_btn.set_tooltip_text("Cerrar [Escape]")
        close_btn.connect("clicked", lambda b: self.destroy())
        btn_box.pack_start(close_btn, False, False, 0)

        h_box.pack_start(btn_box, False, False, 0)

        main_box.pack_start(header, False, False, 0)

        # 2. Pantalla / Display Inset Box
        disp_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        disp_box.get_style_context().add_class("display-box")

        # Línea de Historial / Expresión
        self.hist_label = Gtk.Label(label="Ans = 0")
        self.hist_label.set_xalign(1.0)
        self.hist_label.get_style_context().add_class("history-label")
        disp_box.pack_start(self.hist_label, False, False, 0)

        # Display Principal con 'Press Start 2P'
        self.result_evbox = Gtk.EventBox()
        self.result_label = Gtk.Label(label="0")
        self.result_label.set_xalign(1.0)
        self.result_label.get_style_context().add_class("result-label")
        self.result_evbox.add(self.result_label)
        self.result_evbox.set_tooltip_text("Clic para copiar el resultado al portapapeles (Ctrl+C)")
        self.result_evbox.connect("button-press-event", lambda w, e: self.copy_to_clipboard())
        disp_box.pack_start(self.result_evbox, False, False, 0)

        # Barra de estado inferior del display
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

        status_flower = Gtk.Label(label="🌸")
        status_flower.override_font(Pango.FontDescription("11"))
        status_box.pack_start(status_flower, False, False, 0)

        self.status_left = Gtk.Label(label="Gardevoir OS")
        self.status_left.get_style_context().add_class("status-badge")
        status_box.pack_start(self.status_left, False, False, 0)

        status_spacer = Gtk.Box()
        status_box.pack_start(status_spacer, True, True, 0)

        # Botón Copiar
        self.copy_btn = Gtk.Button(label="󰅍  Copiar")
        self.copy_btn.get_style_context().add_class("header-btn")
        self.copy_btn.set_tooltip_text("Copiar resultado al portapapeles [Ctrl+C]")
        self.copy_btn.connect("clicked", lambda b: self.copy_to_clipboard())
        status_box.pack_start(self.copy_btn, False, False, 0)

        disp_box.pack_start(status_box, False, False, 0)
        main_box.pack_start(disp_box, False, False, 0)

        # 3. Teclado / Grid de Botones
        grid = Gtk.Grid()
        grid.get_style_context().add_class("calc-grid")
        grid.set_row_spacing(6)
        grid.set_column_spacing(6)
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)

        # Definición de botones: (texto, clase, accion, col, row, width, height)
        buttons = [
            # Fila 0
            ("C", "calc-btn-clear", lambda: self.action_clear(), 0, 0, 1, 1),
            ("(", "calc-btn-op", lambda: self.append_token("("), 1, 0, 1, 1),
            (")", "calc-btn-op", lambda: self.append_token(")"), 2, 0, 1, 1),
            ("⌫", "calc-btn-op", lambda: self.action_backspace(), 3, 0, 1, 1),
            ("÷", "calc-btn-op", lambda: self.append_operator("÷"), 4, 0, 1, 1),

            # Fila 1
            ("sin", "calc-btn-fn", lambda: self.append_func("sin("), 0, 1, 1, 1),
            ("cos", "calc-btn-fn", lambda: self.append_func("cos("), 1, 1, 1, 1),
            ("tan", "calc-btn-fn", lambda: self.append_func("tan("), 2, 1, 1, 1),
            ("^", "calc-btn-op", lambda: self.append_operator("^"), 3, 1, 1, 1),
            ("×", "calc-btn-op", lambda: self.append_operator("×"), 4, 1, 1, 1),

            # Fila 2
            ("7", "", lambda: self.append_token("7"), 0, 2, 1, 1),
            ("8", "", lambda: self.append_token("8"), 1, 2, 1, 1),
            ("9", "", lambda: self.append_token("9"), 2, 2, 1, 1),
            ("√", "calc-btn-fn", lambda: self.append_func("sqrt("), 3, 2, 1, 1),
            ("-", "calc-btn-op", lambda: self.append_operator("-"), 4, 2, 1, 1),

            # Fila 3
            ("4", "", lambda: self.append_token("4"), 0, 3, 1, 1),
            ("5", "", lambda: self.append_token("5"), 1, 3, 1, 1),
            ("6", "", lambda: self.append_token("6"), 2, 3, 1, 1),
            ("π", "calc-btn-fn", lambda: self.append_token("π"), 3, 3, 1, 1),
            ("+", "calc-btn-op", lambda: self.append_operator("+"), 4, 3, 1, 1),

            # Fila 4 & 5
            ("1", "", lambda: self.append_token("1"), 0, 4, 1, 1),
            ("2", "", lambda: self.append_token("2"), 1, 4, 1, 1),
            ("3", "", lambda: self.append_token("3"), 2, 4, 1, 1),
            ("%", "calc-btn-op", lambda: self.append_token("%"), 3, 4, 1, 1),
            ("=", "calc-btn-eq", lambda: self.action_calculate(), 4, 4, 1, 2),

            ("0", "", lambda: self.append_token("0"), 0, 5, 1, 1),
            (".", "", lambda: self.append_token("."), 1, 5, 1, 1),
            ("Ans", "calc-btn-fn", lambda: self.append_token("Ans"), 2, 5, 1, 1),
            ("ln", "calc-btn-fn", lambda: self.append_func("ln("), 3, 5, 1, 1),
        ]

        for text, cls, action, col, row, w, h in buttons:
            btn = Gtk.Button(label=text)
            btn.get_style_context().add_class("calc-btn")
            if cls:
                btn.get_style_context().add_class(cls)
            btn.connect("clicked", lambda b, act=action: act())
            grid.attach(btn, col, row, w, h)

        main_box.pack_start(grid, True, True, 0)

    # --- Gestión de Arrastre de Ventana ---
    def on_header_drag(self, widget, event):
        if event.button == 1:
            self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    # --- Acciones de Cálculo ---
    def append_token(self, token):
        if self.just_calculated:
            # Si acaba de calcular y presiona un número o token directo, empezamos nueva cuenta
            if token.isdigit() or token == "(":
                self.current_expr = token
            else:
                self.current_expr = self.current_expr + token
            self.just_calculated = False
        else:
            self.current_expr += token

        self.update_display(self.current_expr or "0")

    def append_operator(self, op):
        if self.just_calculated:
            # Encadenar cálculo usando Ans
            self.current_expr = f"Ans {op} "
            self.just_calculated = False
        else:
            if not self.current_expr:
                self.current_expr = f"Ans {op} "
            else:
                self.current_expr += f" {op} "

        self.update_display(self.current_expr)

    def append_func(self, func_str):
        if self.just_calculated:
            self.current_expr = func_str
            self.just_calculated = False
        else:
            self.current_expr += func_str
        self.update_display(self.current_expr)

    def action_backspace(self):
        if self.just_calculated:
            self.action_clear()
            return
        if self.current_expr:
            # Remover espacios finales o tokens largos
            self.current_expr = self.current_expr.rstrip()
            for fn in ["sqrt(", "sin(", "cos(", "tan(", "ln(", "Ans"]:
                if self.current_expr.endswith(fn):
                    self.current_expr = self.current_expr[:-len(fn)]
                    self.update_display(self.current_expr or "0")
                    return
            self.current_expr = self.current_expr[:-1]
            self.update_display(self.current_expr or "0")

    def action_clear(self):
        self.current_expr = ""
        self.just_calculated = False
        self.update_display("0")

    def action_calculate(self):
        if not self.current_expr:
            return

        expr = self.current_expr
        try:
            val = self.evaluate_math(expr)
            formatted = self.format_val(val)
            self.ans = val
            self.hist_label.set_text(f"{expr} =")
            self.last_result = formatted
            self.current_expr = formatted
            self.just_calculated = True
            self.update_display(formatted)

            if self.config.get("sound", True):
                play_sound(SOUND_FILE, volume=0.35)

        except Exception as e:
            self.hist_label.set_text(f"{expr} =")
            self.update_display("Error")
            self.just_calculated = True

    def evaluate_math(self, expr):
        s = expr.strip()
        s = s.replace('×', '*').replace('÷', '/').replace('^', '**').replace('π', 'pi')
        s = s.replace('Ans', str(self.ans))

        # Multiplicación implícita: 2(3) -> 2*(3), 5pi -> 5*pi, 2sqrt(9) -> 2*sqrt(9)
        s = re.sub(r'(\d)\s*\(', r'\1*(', s)
        s = re.sub(r'\)\s*\(', r')*(', s)
        s = re.sub(r'(\d)\s*(pi|e|sqrt|sin|cos|tan|ln|log|abs)', r'\1*\2', s)
        s = re.sub(r'\)\s*(\d)', r')*\1', s)

        # Porcentaje: 25% -> (25/100.0)
        s = re.sub(r'(\d+(\.\d+)?)%', r'(\1/100.0)', s)

        angle_mode = self.config.get("angle_mode", "DEG")

        env = {
            'pi': math.pi,
            'e': math.e,
            'sqrt': math.sqrt,
            'abs': abs,
            'round': round,
            'fact': math.factorial,
            'ln': math.log,
            'log': math.log10,
        }

        if angle_mode == 'DEG':
            env['sin'] = lambda x: 0.0 if abs(math.sin(math.radians(x))) < 1e-14 else math.sin(math.radians(x))
            env['cos'] = lambda x: 0.0 if abs(math.cos(math.radians(x))) < 1e-14 else math.cos(math.radians(x))
            env['tan'] = lambda x: math.tan(math.radians(x))
            env['asin'] = lambda x: math.degrees(math.asin(x))
            env['acos'] = lambda x: math.degrees(math.acos(x))
            env['atan'] = lambda x: math.degrees(math.atan(x))
        else:
            env['sin'] = math.sin
            env['cos'] = math.cos
            env['tan'] = math.tan
            env['asin'] = math.asin
            env['acos'] = math.acos
            env['atan'] = math.atan

        return eval(s, {'__builtins__': None}, env)

    def format_val(self, val):
        if isinstance(val, (int, float)):
            val = round(val, 12)
            if isinstance(val, float) and val.is_integer():
                return str(int(val))
            formatted = f"{val:.10g}"
            return formatted
        return str(val)

    def update_display(self, text):
        # Ajuste dinámico de fuente para textos largos
        l = len(text)
        if l > 16:
            font_size = "11px"
        elif l > 12:
            font_size = "14px"
        else:
            font_size = "18px"

        self.result_label.set_text(text)
        # Ajustar tamaño de texto en línea
        self.result_label.override_font(Pango.FontDescription(f"Press Start 2P {font_size}"))

    def copy_to_clipboard(self):
        text = self.result_label.get_text()
        if text and text != "Error":
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            clipboard.set_text(text, -1)
            clipboard.store()

            # Feedback visual y sonoro
            self.status_left.set_text("󰄬 ¡Copiado!")
            self.status_left.get_style_context().add_class("status-badge-accent")

            if self.config.get("sound", True):
                play_sound(SOUND_FILE, volume=0.35)

            GLib.timeout_add(1500, self.reset_status)

    def reset_status(self):
        self.status_left.set_text("🌸 Gardevoir OS")
        self.status_left.get_style_context().remove_class("status-badge-accent")
        return False

    def toggle_angle_mode(self, btn=None):
        current = self.config.get("angle_mode", "DEG")
        new_mode = "RAD" if current == "DEG" else "DEG"
        self.config["angle_mode"] = new_mode
        self.angle_btn.set_label(new_mode)
        save_config(self.config)

    def toggle_sound(self, btn=None):
        current = self.config.get("sound", True)
        new_state = not current
        self.config["sound"] = new_state
        self.sound_btn.set_label("󰕾" if new_state else "󰝟")
        save_config(self.config)

    # --- Manejo de Eventos de Teclado ---
    def on_key_press(self, widget, event):
        keyval = event.keyval
        keyname = Gdk.keyval_name(keyval)
        state = event.state

        # Ctrl + C: Copiar resultado
        if (state & Gdk.ModifierType.CONTROL_MASK) and keyname in ['c', 'C']:
            self.copy_to_clipboard()
            return True

        # Ctrl + V: Pegar desde portapapeles
        if (state & Gdk.ModifierType.CONTROL_MASK) and keyname in ['v', 'V']:
            clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
            text = clipboard.wait_for_text()
            if text:
                clean_text = text.strip().replace('\n', '').replace(' ', '')
                self.append_token(clean_text)
            return True

        # Ctrl + Q: Salir
        if (state & Gdk.ModifierType.CONTROL_MASK) and keyname in ['q', 'Q']:
            self.destroy()
            return True

        # Teclas de acción
        if keyname in ['Return', 'KP_Enter', 'equal']:
            self.action_calculate()
            return True
        elif keyname in ['BackSpace']:
            self.action_backspace()
            return True
        elif keyname in ['Escape']:
            if self.current_expr:
                self.action_clear()
            else:
                self.destroy()
            return True
        elif keyname in ['Delete']:
            self.action_clear()
            return True
        elif keyname in ['c', 'C'] and not (state & Gdk.ModifierType.CONTROL_MASK):
            self.action_clear()
            return True
        elif keyname in ['d', 'D']:
            self.toggle_angle_mode()
            return True
        elif keyname in ['s', 'S']:
            self.toggle_sound()
            return True

        # Operadores
        if keyname in ['plus', 'KP_Add']:
            self.append_operator('+')
            return True
        elif keyname in ['minus', 'KP_Subtract']:
            self.append_operator('-')
            return True
        elif keyname in ['asterisk', 'KP_Multiply', 'x', 'X']:
            self.append_operator('×')
            return True
        elif keyname in ['slash', 'KP_Divide']:
            self.append_operator('÷')
            return True
        elif keyname in ['asciicircum']:
            self.append_operator('^')
            return True
        elif keyname in ['percent']:
            self.append_token('%')
            return True
        elif keyname in ['parenleft']:
            self.append_token('(')
            return True
        elif keyname in ['parenright']:
            self.append_token(')')
            return True
        elif keyname in ['period', 'KP_Decimal', 'comma']:
            self.append_token('.')
            return True

        # Números
        if keyname.startswith('KP_') and len(keyname) == 4 and keyname[3].isdigit():
            self.append_token(keyname[3])
            return True
        elif len(keyname) == 1 and keyname.isdigit():
            self.append_token(keyname)
            return True

        return False


def main():
    app = GardevoirCalculator()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    app.present()
    Gtk.main()


if __name__ == "__main__":
    main()
