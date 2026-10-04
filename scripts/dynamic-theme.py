#!/usr/bin/env python3
import sys
import os
import re
import colorsys
import subprocess
import warnings
warnings.filterwarnings('ignore')
from PIL import Image

def extract_colors(image_path):
    try:
        im = Image.open(image_path).convert("RGB")
        w, h = im.size
        
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
        
        sample = im.resize((80, 80), Image.Resampling.BOX)
        best_score = -1.0
        accent_rgb = (0, 212, 212)
        
        for r, g, b in sample.getdata():
            rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
            h, s, v = colorsys.rgb_to_hsv(rf, gf, bf)
            
            if v < 0.35 or s < 0.25:
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
    
    # 1. Cinnamon Theme CSS
    cinnamon_css_override = f"""
/* === GARDEVOIR DYNAMIC ACCENT CSS === */
.panel-top, .panel-bottom, .panel-left, .panel-right {{
    color: #ffffff;
    background-color: rgba({dr}, {dg}, {db}, 0.94);
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
    home = os.path.expanduser("~")
    theme_css_path = os.path.join(home, ".themes/Gardevoir-Dynamic/cinnamon/cinnamon.css")
    if os.path.exists(theme_css_path):
        with open(theme_css_path, "r") as f:
            content = f.read()
        if "/* === GARDEVOIR DYNAMIC ACCENT CSS === */" in content:
            base_content = content.split("/* === GARDEVOIR DYNAMIC ACCENT CSS === */")[0]
        else:
            base_content = content
        with open(theme_css_path, "w") as f:
            f.write(base_content.rstrip() + "\n\n" + cinnamon_css_override.strip() + "\n")
            
        subprocess.run(["gdbus", "call", "--session", "--dest", "org.Cinnamon", "--object-path", "/org/Cinnamon", "--method", "org.Cinnamon.ReloadTheme"], capture_output=True)

    # 2. GLava Bars color
    glava_bars_path = os.path.join(home, ".config/glava/bars.glsl")
    if os.path.exists(glava_bars_path):
        with open(glava_bars_path, "r") as f:
            b_cfg = f.read()
        b_cfg = re.sub(r'#define COLOR \(#[0-9a-fA-F]{6} \* GRADIENT\)', f'#define COLOR ({accent_hex} * GRADIENT)', b_cfg)
        with open(glava_bars_path, "w") as f:
            f.write(b_cfg)

    # 3. Conky accent
    conky_path = os.path.join(home, ".config/conky/gardevoir_glass.conf")
    if os.path.exists(conky_path):
        with open(conky_path, "r") as f:
            conky_cfg = f.read()
        conky_cfg = re.sub(r"color1 = '#[0-9a-fA-F]{6}'", f"color1 = '{accent_hex}'", conky_cfg)
        with open(conky_path, "w") as f:
            f.write(conky_cfg)

    # 4. Rofi cheatsheet
    cheatsheet_rasi = os.path.join(home, ".config/rofi/cheatsheet.rasi")
    if os.path.exists(cheatsheet_rasi):
        with open(cheatsheet_rasi, "r") as f:
            c = f.read()

        # Accent y border-color
        c = re.sub(r'accent:      #[0-9a-fA-F]{6};', f'accent:      {accent_hex};', c)
        c = re.sub(r'border-color: #[0-9a-fA-F]{6};', f'border-color: {accent_hex};', c)

        # Accent-dim (acento oscurecido para bordes sutiles)
        ah, as_, av = colorsys.rgb_to_hsv(ar/255, ag/255, ab/255)
        dim_rf, dim_gf, dim_bf = colorsys.hsv_to_rgb(ah, as_ * 0.8, av * 0.45)
        accent_dim_hex = f"#{int(dim_rf*255):02x}{int(dim_gf*255):02x}{int(dim_bf*255):02x}"
        c = re.sub(r'accent-dim:  #[0-9a-fA-F]{6};', f'accent-dim:  {accent_dim_hex};', c)

        # Fondos derivados del color dominante del wallpaper
        dh_hsv, ds_hsv, dv_hsv = colorsys.rgb_to_hsv(dr/255, dg/255, db/255)

        def bg_shade(v_add, s_factor=1.0):
            rf_, gf_, bf_ = colorsys.hsv_to_rgb(dh_hsv, min(1.0, ds_hsv * s_factor), min(1.0, dv_hsv + v_add))
            return f"#{int(rf_*255):02x}{int(gf_*255):02x}{int(bf_*255):02x}"

        c = re.sub(r'bg:          #[0-9a-fA-F]{6};', f'bg:          {dom_hex};', c)
        c = re.sub(r'bg-mid:      #[0-9a-fA-F]{6};', f'bg-mid:      {bg_shade(0.04)};', c)
        c = re.sub(r'bg-alt:      #[0-9a-fA-F]{6};', f'bg-alt:      {bg_shade(0.08)};', c)
        c = re.sub(r'bg-selected: #[0-9a-fA-F]{6};', f'bg-selected: {bg_shade(0.13, 0.7)};', c)

        with open(cheatsheet_rasi, "w") as f:
            f.write(c)

    # 5. OpenRGB
    subprocess.run(["openrgb", "--device", "1", "--mode", "Direct", "--color", accent_hex[1:]], capture_output=True)
    subprocess.run(["openrgb", "--device", "0", "--mode", "Static", "--color", accent_hex[1:]], capture_output=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        img = sys.argv[1]
    else:
        p = subprocess.run(["gsettings", "get", "org.cinnamon.desktop.background", "picture-uri"], capture_output=True, text=True)
        img = p.stdout.strip().replace("'", "").replace("file://", "")
        
    if os.path.exists(img):
        dom_color, accent_color = extract_colors(img)
        update_system_theme(dom_color, accent_color)
