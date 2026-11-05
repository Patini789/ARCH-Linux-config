#!/usr/bin/env python3
"""
Toggle / Switch Keyboard Layout for Cinnamon Desktop
Integrates with Cinnamon DBus (updates panel applet, system state, and notifications).
"""

import sys
import subprocess
import os

try:
    from gi.repository import Gio, GLib
except ImportError:
    Gio = None
    GLib = None

SOUND_EFFECT = os.path.expanduser("~/.local/share/sounds/pokemon/pokeball_blip.wav")

def play_sound():
    if os.path.exists(SOUND_EFFECT):
        try:
            subprocess.Popen(
                ["pw-play", "--volume=0.35", SOUND_EFFECT],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass

def send_notification(title, message, icon="input-keyboard"):
    try:
        subprocess.Popen(
            [
                "notify-send",
                "-t", "1300",
                "-h", "string:x-canonical-private-synchronous:keyboard-layout",
                "-i", icon,
                title,
                message
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

def switch_via_cinnamon(target=None):
    if not Gio or not GLib:
        return False

    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        proxy = Gio.DBusProxy.new_sync(
            bus,
            Gio.DBusProxyFlags.NONE,
            None,
            "org.Cinnamon",
            "/org/Cinnamon",
            "org.Cinnamon",
            None
        )

        res = proxy.call_sync("GetInputSources", None, Gio.DBusCallFlags.NONE, 1000, None)
        if not res:
            return False

        sources = res.unpack()[0]
        if not sources:
            return False

        curr_idx = 0
        for i, s in enumerate(sources):
            # s[11] is boolean indicating active state
            if s[11]:
                curr_idx = i
                break

        if target is not None:
            target_str = target.lower()
            if target_str in ("latam", "es", "spanish", "español", "espanol", "0"):
                next_idx = 0
            elif target_str in ("us", "en", "english", "ingles", "inglés", "1"):
                next_idx = 1 if len(sources) > 1 else 0
            else:
                next_idx = (curr_idx + 1) % len(sources)
        else:
            next_idx = (curr_idx + 1) % len(sources)

        proxy.call_sync(
            "ActivateInputSourceIndex",
            GLib.Variant("(i)", (next_idx,)),
            Gio.DBusCallFlags.NONE,
            1000,
            None
        )

        new_source = sources[next_idx]
        lang_id = new_source[1]  # 'latam', 'us', etc.
        lang_name = new_source[3] # 'Español (latinoamericano)', etc.

        if "us" in lang_id.lower() or "en" in lang_id.lower():
            flag = "🇺🇸"
            short = "US"
        else:
            flag = "🇲🇽"
            short = "ES"

        send_notification(
            f"Teclado: {short} {flag}",
            f"{lang_name}"
        )
        play_sound()
        return True
    except Exception as e:
        return False

def fallback_setxkbmap(target=None):
    try:
        out = subprocess.check_output(["setxkbmap", "-query"], text=True)
        current = "latam"
        for line in out.splitlines():
            if line.startswith("layout:"):
                current = line.split(":", 1)[1].strip().split(",")[0]
                break

        if target:
            t = target.lower()
            if t in ("us", "en", "english", "ingles", "inglés"):
                new_layout = "us"
            else:
                new_layout = "latam"
        else:
            new_layout = "us" if current == "latam" else "latam"

        subprocess.run(["setxkbmap", new_layout], check=True)
        if new_layout == "us":
            send_notification("Teclado: US 🇺🇸", "Inglés (EE. UU.)")
        else:
            send_notification("Teclado: ES 🇲🇽", "Español (latinoamericano)")
        play_sound()
        return True
    except Exception:
        return False

def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None
    if not switch_via_cinnamon(target):
        fallback_setxkbmap(target)

if __name__ == "__main__":
    main()
