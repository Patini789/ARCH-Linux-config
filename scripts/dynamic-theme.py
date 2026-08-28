#!/usr/bin/env python3
import sys
import os
import re
import colorsys
import subprocess
from PIL import Image

HOME = os.path.expanduser("~")

def extract_colors(image_path):
    try:
        im = Image.open(image_path).convert("RGB")
        w, h = im.size
        
        # 1. Color dominante base (40% inferior para el panel)
        bottom_crop = im.crop((0, int(h * 0.4), w, h)).resize((60, 60), Image.Resampling.BOX)
        quantized = bottom_crop.quantize(colors=12, method=Image.Quantize.MEDIANCUT)
        palette = quantized.getpalette()[:36]
        
        color_counts = quantized.getcolors()
        color_counts.sort(key=lambda x: x[0], reverse=True)
        
        dom_idx = color_counts[0][1]
        raw_r, raw_g, raw_b = palette[dom_idx*3 : dom_idx*3 + 3]
        
        dh, ds, dv = colorsys.rgb_to_hsv(raw_r / 255.0, raw_g / 255.0, raw_b / 255.0)
        target_v = min(0.18, max(0.10, dv * 0.35))
        target_s = min(0.55, ds * 1.1)
        
        dom_rf, dom_gf, dom_bf = colorsys.hsv_to_rgb(dh, target_s, target_v)
        dom_r, dom_g, dom_b = int(dom_rf * 255), int(dom_gf * 255), int(dom_bf * 255)
        
        # 2. Color de acento (el más saturado y vibrante de la imagen)
        sample = im.resize((80, 80), Image.Resampling.BOX)
        best_score = -1.0
        accent_rgb = (0, 212, 212)
        
        # Usar get_flattened_data si existe o getdata
        data = getattr(sample, 'get_flattened_data', sample.getdata)()
        for r, g, b in data:
            rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
            h, s, v = colorsys.rgb_to_hsv(rf, gf, bf)
            
            if v < 0.25 or s < 0.20:
                continue
            
            score = (s ** 2.0) * (v ** 1.0)
            if score > best_score:
                best_score = score
                accent_rgb = (r, g, b)
                
        return (dom_r, dom_g, dom_b), accent_rgb
    except Exception as e:
        print(f"Error extrayendo colores: {e}")
        return (26, 26, 36), (0, 212, 212)

def update_system_theme(dom_rgb, accent_rgb):
    dr, dg, db = dom_rgb
    ar, ag, ab = accent_rgb
    
    dom_hex = f"#{dr:02x}{dg:02x}{db:02x}"
    accent_hex = f"#{ar:02x}{ag:02x}{ab:02x}"
    
    # 1. CINNAMON PANEL THEME CSS (80% translucidez + outline superior dinámico)
    cinnamon_css_override = f"""
/* === GARDEVOIR DYNAMIC ACCENT CSS === */
.panel-top, .panel-bottom, .panel-left, .panel-right {{
    color: #ffffff;
    background-color: rgba({dr}, {dg}, {db}, 0.82);
    font-weight: bold;
}}

.panel-bottom {{
    box-shadow: inset 0 2px 0 0 {accent_hex};
}}

.panel-top {{
    box-shadow: inset 0 -2px 0 0 {accent_hex};
}}

.grouped-window-list-item-box:active, .grouped-window-list-item-box:checked {{
    background-color: rgba({ar}, {ag}, {ab}, 0.25);
    box-shadow: inset 0 2px 0 0 {accent_hex};
    border-radius: 4px;
}}

.grouped-window-list-item-box:hover {{
    background-color: rgba(255, 255, 255, 0.10);
    border-radius: 4px;
}}

.grouped-window-list-badge {{
    background-color: {accent_hex};
    color: #11111b;
    font-weight: bold;
}}

.applet-box:hover, .applet-box:active {{
    background-color: rgba(255, 255, 255, 0.10);
    border-radius: 4px;
}}

#menu-search-entry, #appmenu-search-entry {{
    selection-background-color: {accent_hex};
    selected-color: #11111b;
    border: 1px solid rgba({ar}, {ag}, {ab}, 0.6);
}}
"""
    theme_css_path = os.path.join(HOME, ".themes/Gardevoir-Dynamic/cinnamon/cinnamon.css")
    if os.path.exists(theme_css_path):
        with open(theme_css_path, "r") as f:
            content = f.read()
        if "/* === GARDEVOIR DYNAMIC ACCENT CSS === */" in content:
            base_content = content.split("/* === GARDEVOIR DYNAMIC ACCENT CSS === */")[0]
        else:
            base_content = content
        with open(theme_css_path, "w") as f:
            f.write(base_content.rstrip() + "\n\n" + cinnamon_css_override.strip() + "\n")
        
        # Recargar tema de Cinnamon por DBus limpiamente sin parpadeos
        subprocess.run(["gdbus", "call", "--session", "--dest", "org.Cinnamon", "--object-path", "/org/Cinnamon", "--method", "org.Cinnamon.ReloadTheme"], capture_output=True)

    # 2. GTK 3 & GTK 4 THEME
    gtk_css = f"""
/* Transparencia en Ventanas y Barras Superiores */
window.background, .window-frame, window {{
    background-color: rgba({dr}, {dg}, {db}, 0.82) !important;
}}

headerbar, .titlebar, window decoration {{
    background-color: rgba({dr}, {dg}, {db}, 0.85) !important;
    border-top: 2px solid {accent_hex} !important;
    box-shadow: inset 0 1px 0 0 {accent_hex} !important;
}}

headerbar:backdrop, .titlebar:backdrop {{
    background-color: rgba({dr}, {dg}, {db}, 0.80) !important;
    border-top: 2px solid rgba({ar}, {ag}, {ab}, 0.4) !important;
}}

*:selected, entry selection, textview text selection {{
    background-color: {accent_hex} !important;
    color: #11111b !important;
}}
"""
    for gtk_dir in [os.path.join(HOME, ".config/gtk-3.0"), os.path.join(HOME, ".config/gtk-4.0")]:
        os.makedirs(gtk_dir, exist_ok=True)
        with open(os.path.join(gtk_dir, "gtk.css"), "w") as f:
            f.write(gtk_css.strip() + "\n")

    # 3. ROFI LAUNCHER CONFIG
    rofi_rasi = f"""configuration {{
    modi: "drun,window,run";
    show-icons: true;
    icon-theme: "Papirus-Dark";
    display-drun: "󰍉 ";
    display-window: "🪟 ";
    display-run: "⚡ ";
    drun-display-format: "{{name}}";
    font: "Inter 12";
}}

@theme "/dev/null"

* {{
    bg: rgba({dr}, {dg}, {db}, 0.90);
    bg-alt: rgba(255, 255, 255, 0.07);
    fg: #e2e8f0;
    fg-dim: #94a3b8;
    accent: {accent_hex};
    border-color: {accent_hex};
    
    background-color: transparent;
    text-color: @fg;
    margin: 0;
    padding: 0;
}}

window {{
    background-color: @bg;
    border: 2px;
    border-color: @border-color;
    border-radius: 18px;
    width: 660px;
    location: center;
    anchor: center;
    padding: 24px;
}}

inputbar {{
    background-color: @bg-alt;
    border: 1px;
    border-color: rgba({ar}, {ag}, {ab}, 0.40);
    border-radius: 12px;
    padding: 12px 18px;
    margin: 0 0 16px 0;
    children: [ prompt, entry ];
}}

prompt {{
    text-color: @accent;
    margin: 0 10px 0 0;
    font: "Inter Bold 13";
}}

entry {{
    placeholder: "Buscar aplicaciones...";
    placeholder-color: @fg-dim;
    text-color: #ffffff;
    font: "Inter 12";
}}

listview {{
    lines: 7;
    columns: 1;
    fixed-height: true;
    scrollbar: false;
    spacing: 6px;
    cycle: true;
}}

element {{
    padding: 10px 14px;
    border-radius: 10px;
    border: 1px;
    border-color: transparent;
}}

element selected {{
    background-color: rgba({ar}, {ag}, {ab}, 0.22);
    border: 1px;
    border-color: @accent;
    text-color: #ffffff;
}}

element-icon {{
    size: 34px;
    margin: 0 14px 0 4px;
}}

element-text {{
    vertical-align: 0.5;
    text-color: inherit;
    font: "Inter SemiBold 12";
}}
"""
    with open(os.path.join(HOME, ".config/rofi/config.rasi"), "w") as f:
        f.write(rofi_rasi)

    # 4. GLAVA AUDIO VISUALIZER (Sincronización de color dinámico sobre el panel)
    glava_bars_path = os.path.join(HOME, ".config/glava/bars.glsl")
    if os.path.exists(glava_bars_path):
        bars_content = f"""/* Center line thickness (pixels) */
#define C_LINE 1
/* Width (in pixels) of each bar */
#define BAR_WIDTH 4
/* Width (in pixels) of each bar gap */
#define BAR_GAP 2
/* Outline color */
#define BAR_OUTLINE #262626
/* Outline width (in pixels, set to 0 to disable outline drawing) */
#define BAR_OUTLINE_WIDTH 0
/* Amplify magnitude of the results each bar displays */
#define AMPLIFY 280
/* Whether the current settings use the alpha channel */
#define USE_ALPHA 0
/* How strong the gradient changes */
#define GRADIENT_POWER 70
/* Bar color changes with height */
#define GRADIENT (d / GRADIENT_POWER + 1)
/* Bar color - Synced with dynamic accent */
#define COLOR ({accent_hex} * GRADIENT)
/* Direction that the bars are facing, 0 for inward, 1 for outward */
#define DIRECTION 0
/* Whether to switch left/right audio buffers */
#define INVERT 0
/* Whether to flip the output vertically */
#define FLIP 0
/* Mirror options */
#define MIRROR_YX 0
"""
        with open(glava_bars_path, "w") as f:
            f.write(bars_content)
        subprocess.run(["systemctl", "--user", "restart", "glava.service"], capture_output=True)

    # 5. CONKY WIDGET DYNAMIC COLOR ACCENT
    conky_path = os.path.join(HOME, ".config/conky/gardevoir_glass.conf")
    if os.path.exists(conky_path):
        with open(conky_path, "r") as f:
            conky_cfg = f.read()
        conky_cfg = re.sub(r"color1 = '#[0-9a-fA-F]{6}'", f"color1 = '{accent_hex}'", conky_cfg)
        with open(conky_path, "w") as f:
            f.write(conky_cfg)
        subprocess.run(["pkill", "-USR1", "conky"], capture_output=True)

    # 6. CHEATSHEET ROFI
    cheatsheet_rasi = os.path.join(HOME, ".config/rofi/cheatsheet.rasi")
    if os.path.exists(cheatsheet_rasi):
        with open(cheatsheet_rasi, "r") as f:
            c = f.read()
        c = re.sub(r'accent: #[0-9a-fA-F]{6};', f'accent: {accent_hex};', c)
        c = re.sub(r'border-color: #[0-9a-fA-F]{6};', f'border-color: {accent_hex};', c)
        with open(cheatsheet_rasi, "w") as f:
            f.write(c)

    # 7. HARDWARE RGB (Teclado y Ratón)
    subprocess.run(["openrgb", "--device", "1", "--mode", "Direct", "--color", accent_hex[1:]], capture_output=True)
    subprocess.run(["openrgb", "--device", "0", "--mode", "Static", "--color", accent_hex[1:]], capture_output=True)
    
    print(f"Sistema completo sincronizado: Base 80% {dom_hex} | Outline & GLava {accent_hex}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        img = sys.argv[1]
    else:
        p = subprocess.run(["gsettings", "get", "org.cinnamon.desktop.background", "picture-uri"], capture_output=True, text=True)
        img = p.stdout.strip().replace("'", "").replace("file://", "")
        
    if os.path.exists(img):
        dom_color, accent_color = extract_colors(img)
        update_system_theme(dom_color, accent_color)
    else:
        print(f"Imagen no encontrada: {img}")
