#!/usr/bin/env python3
import subprocess
import time
import os

env = os.environ.copy()
env.setdefault('DISPLAY', ':0')
env.setdefault('XAUTHORITY', os.path.expanduser('~/.Xauthority'))

OPACITY_EDITORS = "4166118276" # 97% Opacidad (Antigravity, VS Code, Godot - Máxima legibilidad)
OPACITY_BRAVE   = "4080218930" # 95% Opacidad (Brave)
OPACITY_APPS    = "4037269257" # 94% Opacidad (Nemo, Discord, otras apps)
OPACITY_FULLSCREEN = "4080218930" # 95% Opacidad en pantalla completa
OPACITY_VIDEO_FULLSCREEN = "4294967295" # 100% para vídeos a pantalla completa

EDITOR_CLASSES   = ['code', 'vscodium', 'antigravity', 'godot', 'sublime', 'cursor']
TERMINAL_CLASSES = ['kitty', 'gnome-terminal', 'org.gnome.terminal', 'x-terminal-emulator']
VIDEO_CLASSES    = ['brave', 'firefox', 'chromium', 'librewolf', 'discord', 'vlc', 'mpv', 'celluloid']

def sync():
    try:
        p = subprocess.run(['xdotool', 'search', '--onlyvisible', '--class', '.*'], capture_output=True, text=True, env=env)
        wids = p.stdout.strip().split()
        
        for wid in wids:
            cp = subprocess.run(['xprop', '-id', wid, 'WM_CLASS', '_NET_WM_STATE'], capture_output=True, text=True, env=env)
            info = cp.stdout.lower()
            
            if 'wm_class:  not found' in info:
                continue
            if 'nemo-desktop' in info or 'cinnamon' in info or 'conky' in info:
                continue
                
            # Solo F11/video: maximizar no debe contar como pantalla completa.
            is_fullscreen = '_net_wm_state_fullscreen' in info
                    
            # Apps en fullscreen conservan transparencia; multimedia se vuelve sólido.
            if is_fullscreen:
                target = OPACITY_VIDEO_FULLSCREEN if any(app in info for app in VIDEO_CLASSES) else OPACITY_FULLSCREEN
                subprocess.run(['xprop', '-id', wid, '-f', '_NET_WM_WINDOW_OPACITY', '32c', '-set', '_NET_WM_WINDOW_OPACITY', target], capture_output=True, env=env)
                continue
                
            # 2. MODO VENTANA -> Asignar opacidad correspondiente
            if any(ed in info for ed in EDITOR_CLASSES):
                target = OPACITY_EDITORS
            elif 'brave' in info:
                target = OPACITY_BRAVE
            elif any(term in info for term in TERMINAL_CLASSES):
                # Kitty ya gestiona su propia transparencia; no acumular otra
                # capa de opacidad X11 encima de background_opacity.
                subprocess.run(['xprop', '-id', wid, '-remove', '_NET_WM_WINDOW_OPACITY'], capture_output=True, env=env)
                continue
            else:
                target = OPACITY_APPS
                
            subprocess.run(['xprop', '-id', wid, '-f', '_NET_WM_WINDOW_OPACITY', '32c', '-set', '_NET_WM_WINDOW_OPACITY', target], capture_output=True, env=env)
    except Exception:
        pass

if __name__ == "__main__":
    time.sleep(1.0)
    while True:
        sync()
        time.sleep(1.0)
