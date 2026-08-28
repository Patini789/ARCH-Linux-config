#!/usr/bin/env python3
import os
import glob
from PIL import Image, ImageFilter, ImageEnhance

INPUT_DIR = os.path.join(os.path.expanduser("~"), "Pictures/Gardevoir")
OUTPUT_DIR = os.path.join(INPUT_DIR, "Blur_16x9")
os.makedirs(OUTPUT_DIR, exist_ok=True)

TARGET_W = 3840
TARGET_H = 2160

supported_exts = ("*.png", "*.jpg", "*.jpeg")
files = []
for ext in supported_exts:
    files.extend(glob.glob(os.path.join(INPUT_DIR, ext)))

print(f"Encontradas {len(files)} imágenes para procesar...")

for img_path in files:
    filename = os.path.basename(img_path)
    # Evitar recursión o archivos temporales
    if "blur" in filename.lower() or os.path.dirname(img_path) == OUTPUT_DIR:
        continue
    
    out_path = os.path.join(OUTPUT_DIR, f"{os.path.splitext(filename)[0]}_blur.png")
    
    try:
        with Image.open(img_path) as im:
            im = im.convert("RGBA")
            orig_w, orig_h = im.size
            aspect = orig_w / orig_h
            
            # Si ya es panorámica amplia (16:9 o más ancha), la copiamos directamente o redimensionamos
            if aspect >= 1.6:
                # Ya es horizontal panorámica
                continue
            
            print(f"Transformando imagen vertical: {filename} ({orig_w}x{orig_h})")
            
            # 1. Crear el fondo difuminado (Background)
            # Escalar para cubrir 3840x2160 (Crop to fill)
            bg_scale = max(TARGET_W / orig_w, TARGET_H / orig_h)
            bg_w = int(orig_w * bg_scale)
            bg_h = int(orig_h * bg_scale)
            bg = im.resize((bg_w, bg_h), Image.Resampling.LANCZOS)
            
            # Centrar el recorte del fondo
            left = (bg_w - TARGET_W) // 2
            top = (bg_h - TARGET_H) // 2
            bg = bg.crop((left, top, left + TARGET_W, top + TARGET_H))
            
            # Aplicar desenfoque gaussiano suave y oscurecer un 35% para que resalte el centro
            bg = bg.filter(ImageFilter.GaussianBlur(radius=45))
            enhancer = ImageEnhance.Brightness(bg.convert("RGB"))
            bg = enhancer.enhance(0.65).convert("RGBA")
            
            # 2. Escalar el primer plano (Foreground) para que encaje al 100% de la altura
            fg_h = TARGET_H
            fg_w = int(orig_w * (fg_h / orig_h))
            fg = im.resize((fg_w, fg_h), Image.Resampling.LANCZOS)
            
            # 3. Crear sombra suave para separar el centro del fondo
            shadow = Image.new("RGBA", (fg_w + 60, fg_h), (0, 0, 0, 0))
            shadow_mask = Image.new("RGBA", (fg_w, fg_h), (0, 0, 0, 160))
            shadow.paste(shadow_mask, (30, 0))
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=25))
            
            # 4. Pegar todo en el lienzo 16:9
            fg_x = (TARGET_W - fg_w) // 2
            bg.paste(shadow, (fg_x - 30, 0), shadow)
            bg.paste(fg, (fg_x, 0), fg)
            
            # Guardar en alta calidad
            bg.convert("RGB").save(out_path, "PNG", optimize=True)
            print(f"  -> Guardada en: {out_path}")
            
    except Exception as e:
        print(f"Error procesando {filename}: {e}")

print("¡Proceso de desenfoque completado con éxito!")
