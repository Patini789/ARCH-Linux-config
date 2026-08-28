#!/usr/bin/env python3
import subprocess
import time
import os

def session_env():
    # Resolver DISPLAY y XAUTHORITY dinámicamente para que el script funcione
    # en cualquier sesión X (no hardcoded a :0).
    env = dict(os.environ)
    if not env.get("DISPLAY"):
        try:
            out = subprocess.run(["xdotool", "getmouselocation"], capture_output=True, text=True)
            m = out.stdout.split("screen:")[-1].strip()
            if m:
                env["DISPLAY"] = ":" + m.split(".")[0]
        except Exception:
            pass
    if not env.get("XAUTHORITY"):
        xa = os.path.join(os.path.expanduser("~"), ".Xauthority")
        if os.path.exists(xa):
            env["XAUTHORITY"] = xa
    return env

env = session_env()

OPACITY_BRAVE = "4252017622" # 99% Opacidad (Brave)
OPACITY_APPS  = "4166118276" # 97% Opacidad (Antigravity, Nemo)
OPACITY_TERM  = "3865470565" # 90% Opacidad (Kitty, Terminales)

TERMINAL_CLASSES = ['kitty', 'gnome-terminal', 'org.gnome.terminal', 'x-terminal-emulator']
# Verificar solo las propiedades que realmente interesan; evita relanzar xprop
# para ventanas ya conocidas y sin cambios.
_last_state = {}

def get_windows():
    try:
        p = subprocess.run(['xdotool', 'search', '--onlyvisible', '--class', '.*'],
                           capture_output=True, text=True, env=env)
        return p.stdout.strip().split()
    except Exception:
        return []

def apply_opacity(wid, target):
    subprocess.run(['xprop', '-id', wid, '-f', '_NET_WM_WINDOW_OPACITY', '32c',
                    '-set', '_NET_WM_WINDOW_OPACITY', target], capture_output=True, env=env)

def sync():
    try:
        wids = get_windows()
        for wid in wids:
            # Cachear por ventana para no repetir xprop si no cambió de estado.
            cp = subprocess.run(['xprop', '-id', wid, 'WM_CLASS', '_NET_WM_STATE'],
                                capture_output=True, text=True, env=env)
            info = cp.stdout.lower()

            if 'wm_class:  not found' in info:
                continue
            if 'nemo-desktop' in info or 'cinnamon' in info or 'conky' in info:
                continue

            is_fullscreen = '_net_wm_state_fullscreen' in info

            if not is_fullscreen:
                geo_p = subprocess.run(['xdotool', 'getwindowgeometry', wid],
                                       capture_output=True, text=True, env=env)
                geo = geo_p.stdout
                if ('1920x1080' in geo or '1824x1026' in geo) and ('0,0' in geo or '1920,0' in geo):
                    is_fullscreen = True

            if is_fullscreen:
                if _last_state.get(wid) != 'fs':
                    subprocess.run(['xprop', '-id', wid, '-remove', '_NET_WM_WINDOW_OPACITY'],
                                   capture_output=True, env=env)
                    _last_state[wid] = 'fs'
            else:
                if 'brave' in info:
                    target = OPACITY_BRAVE
                elif any(term in info for term in TERMINAL_CLASSES):
                    target = OPACITY_TERM
                else:
                    target = OPACITY_APPS
                if _last_state.get(wid) != target:
                    apply_opacity(wid, target)
                    _last_state[wid] = target
    except Exception:
        pass

if __name__ == "__main__":
    while True:
        sync()
        time.sleep(1.0)
