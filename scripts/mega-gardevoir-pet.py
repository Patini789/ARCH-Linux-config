#!/usr/bin/env python3
"""
Mega-Gardevoir Shiny Desktop Pet (Shimeji Nativo)
Personalizado para Cinnamon / X11 en Arch Linux.
Soporte multi-monitor (pantalla 1 y 2), deteccion de pantalla completa (se oculta detras),
plataformas en ventanas X11, fisicas reales, giros fluidos y cero emojis.
"""

import os
import sys
import time
import random
import re
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import cairo

SPRITES_DIR = os.path.expanduser("~/Pictures/Gardevoir_Sprites")
SOUNDS_DIR = os.path.expanduser("~/.local/share/sounds/pokemon")

DIR_DOWN       = 0
DIR_DOWN_RIGHT = 1
DIR_RIGHT      = 2
DIR_UP_RIGHT   = 3
DIR_UP         = 4
DIR_UP_LEFT    = 5
DIR_LEFT       = 6
DIR_DOWN_LEFT  = 7

ANCHORS = {
    'Walk':   (16, 26),
    'Idle':   (16, 30),
    'Hop':    (16, 50),
    'Rotate': (16, 26),
    'Sleep':  (12, 22),
    'Appeal': (20, 30),
    'Attack': (36, 46),
    'Hurt':   (20, 34)
}

class SpriteManager:
    def __init__(self, sprites_dir, scale=2.0):
        self.sprites_dir = sprites_dir
        self.scale = scale
        self.anims = {}
        self.load_metadata()
        self.load_sprites()

    def load_metadata(self):
        xml_path = os.path.join(self.sprites_dir, 'AnimData.xml')
        self.meta = {}
        if os.path.exists(xml_path):
            tree = ET.parse(xml_path)
            root = tree.getroot()
            anims = root.find('Anims')
            if anims is not None:
                for a in anims.findall('Anim'):
                    name = a.find('Name')
                    if name is not None and name.text:
                        n = name.text
                        fw = a.find('FrameWidth')
                        fh = a.find('FrameHeight')
                        durs = [int(d.text) for d in a.findall('Durations/Duration')]
                        self.meta[n] = {
                            'fw': int(fw.text) if fw is not None else 32,
                            'fh': int(fh.text) if fh is not None else 40,
                            'durations': durs if durs else [6]
                        }

    def pil_to_pixbuf(self, pil_img):
        data = pil_img.tobytes()
        w, h = pil_img.size
        has_alpha = pil_img.mode == 'RGBA'
        rowstride = w * (4 if has_alpha else 3)
        pb = GdkPixbuf.Pixbuf.new_from_bytes(
            GLib.Bytes.new(data),
            GdkPixbuf.Colorspace.RGB,
            has_alpha,
            8,
            w,
            h,
            rowstride
        )
        scaled_w = max(1, int(w * self.scale))
        scaled_h = max(1, int(h * self.scale))
        return pb.scale_simple(scaled_w, scaled_h, GdkPixbuf.InterpType.NEAREST)

    def load_sprites(self):
        needed = ['Walk', 'Idle', 'Hop', 'Rotate', 'Sleep', 'Appeal', 'Attack', 'Hurt']
        for name in needed:
            sheet_path = os.path.join(self.sprites_dir, f'{name}-Anim.png')
            if not os.path.exists(sheet_path):
                continue
            
            im = Image.open(sheet_path).convert('RGBA')
            fw = self.meta.get(name, {}).get('fw', 32)
            fh = self.meta.get(name, {}).get('fh', 40)
            durs = self.meta.get(name, {}).get('durations', [6])
            
            cols = im.width // fw
            rows = im.height // fh
            
            frames_by_dir = {}
            for r in range(rows):
                dir_frames = []
                for c in range(cols):
                    crop = im.crop((c * fw, r * fh, (c + 1) * fw, (r + 1) * fh))
                    dir_frames.append(self.pil_to_pixbuf(crop))
                frames_by_dir[r] = dir_frames
                
            self.anims[name] = {
                'frames': frames_by_dir,
                'durations': durs,
                'fw': fw,
                'fh': fh,
                'cols': cols,
                'rows': rows,
                'anchor': ANCHORS.get(name, (fw // 2, fh // 2))
            }


class SystemMonitor:
    """Escanea ventanas abiertas en X11 y monitorea el modo pantalla completa."""
    def __init__(self):
        self.last_scan = 0
        self.cached_windows = []
        self.fullscreen_rects = []

    def scan(self, force=False):
        now = time.time()
        if not force and (now - self.last_scan < 0.8):
            return self.cached_windows, self.fullscreen_rects
            
        self.last_scan = now
        windows = []
        fs_rects = []
        try:
            out = subprocess.check_output(['xprop', '-root', '_NET_CLIENT_LIST_STACKING'], stderr=subprocess.DEVNULL).decode()
            wids = re.findall(r'0x[0-9a-fA-F]+', out)
            for wid in reversed(wids):
                try:
                    state = subprocess.check_output(['xprop', '-id', wid, '_NET_WM_STATE'], stderr=subprocess.DEVNULL).decode()
                    if '_NET_WM_STATE_HIDDEN' in state:
                        continue
                    wm_class = subprocess.check_output(['xprop', '-id', wid, 'WM_CLASS'], stderr=subprocess.DEVNULL).decode().lower()
                    if any(k in wm_class for k in ['cinnamon', 'nemo-desktop', 'gardevoir', 'glava', 'conky']):
                        continue
                        
                    geo_out = subprocess.check_output(['xwininfo', '-id', wid], stderr=subprocess.DEVNULL).decode()
                    x = int(re.search(r'Absolute upper-left X:\s+(-?\d+)', geo_out).group(1))
                    y = int(re.search(r'Absolute upper-left Y:\s+(-?\d+)', geo_out).group(1))
                    w = int(re.search(r'Width:\s+(\d+)', geo_out).group(1))
                    h = int(re.search(r'Height:\s+(\d+)', geo_out).group(1))
                    
                    if '_NET_WM_STATE_FULLSCREEN' in state:
                        fs_rects.append({'x1': x, 'y1': y, 'x2': x + w, 'y2': y + h})
                        
                    if w > 150 and h > 100 and y >= 0:
                        windows.append({'x': x, 'y': y, 'w': w, 'h': h, 'name': wm_class.split()[-1].strip('\"')})
                except Exception:
                    continue
        except Exception:
            pass
            
        self.cached_windows = windows
        self.fullscreen_rects = fs_rects
        return windows, fs_rects


class GardevoirPet(Gtk.Window):
    def __init__(self, scale=2.0):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.scale = scale
        self.sprite_mgr = SpriteManager(SPRITES_DIR, scale=self.scale)
        self.monitor_mgr = SystemMonitor()
        
        self.set_title("Mega-Gardevoir-Pet")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.UTILITY)
        self.set_app_paintable(True)
        
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)
            
        self.connect('draw', self.on_draw)
        self.connect('button-press-event', self.on_button_press)
        self.connect('button-release-event', self.on_button_release)
        self.connect('motion-notify-event', self.on_motion_notify)
        
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )
        
        self.canvas_w = int(80 * self.scale)
        self.canvas_h = int(96 * self.scale)
        self.ground_x = self.canvas_w // 2
        self.ground_y = self.canvas_h - int(4 * self.scale)
        self.set_size_request(self.canvas_w, self.canvas_h)
        
        self.update_monitors_geometry()
        
        # Iniciar en monitor primario
        self.current_platform = self.get_base_platform_at(self.total_min_x + 300)
        self.x = float(self.current_platform['x1'] + 200)
        self.y = float(self.current_platform['y'])
        
        # Animacion y estados
        self.current_anim = 'Walk'
        self.direction = DIR_RIGHT
        self.frame_idx = 0
        self.tick_counter = 0
        self.state = 'WALK'
        self.state_timer = 200
        
        # Interaccion y arrastre
        self.is_dragging = False
        self.drag_offset_x = 0.0
        self.drag_offset_y = 0.0
        self.vy = 0.0
        self.sound_enabled = True
        self.last_click_time = 0
        self.is_behind_fullscreen = False
        
        self.show_all()
        self.move(int(self.x), int(self.y))
        
        GLib.timeout_add(33, self.on_tick)
        self.play_sound('shiny_sparkle.wav')

    def update_monitors_geometry(self):
        display = Gdk.Display.get_default()
        n = display.get_n_monitors()
        self.monitors = []
        self.total_min_x = 0
        self.total_max_x = 1920
        
        for i in range(n):
            m = display.get_monitor(i)
            geo = m.get_geometry()
            work = m.get_workarea()
            # Altura util respecto al panel de este monitor
            base_floor_y = work.y + work.height - self.ground_y
            self.monitors.append({
                'id': i,
                'x1': geo.x,
                'x2': geo.x + geo.width,
                'y1': geo.y,
                'y2': geo.y + geo.height,
                'floor_y': base_floor_y
            })
            
        if self.monitors:
            self.total_min_x = min(m['x1'] for m in self.monitors)
            self.total_max_x = max(m['x2'] for m in self.monitors) - self.canvas_w

    def get_base_platform_at(self, foot_x):
        for m in self.monitors:
            if m['x1'] <= foot_x <= m['x2']:
                return {
                    'x1': m['x1'] + 10,
                    'x2': m['x2'] - self.canvas_w - 10,
                    'y': m['floor_y'],
                    'name': f'monitor_{m["id"]}'
                }
        # Fallback al primer monitor
        return {
            'x1': 10,
            'x2': self.total_max_x - 10,
            'y': self.monitors[0]['floor_y'] if self.monitors else 848,
            'name': 'fallback_base'
        }

    def get_all_platforms(self, foot_x):
        platforms = [self.get_base_platform_at(foot_x)]
        windows, _ = self.monitor_mgr.scan()
        for w in windows:
            p_y = w['y'] - self.ground_y
            if p_y >= -30:
                platforms.append({
                    'x1': w['x'],
                    'x2': w['x'] + w['w'] - self.canvas_w,
                    'y': p_y,
                    'name': w['name']
                })
        return platforms

    def find_landing_platform(self, foot_x, cur_window_y):
        platforms = self.get_all_platforms(foot_x)
        candidates = []
        for p in platforms:
            if p['x1'] - 15 <= foot_x <= p['x2'] + self.canvas_w + 15:
                if p['y'] >= (cur_window_y - 15):
                    candidates.append(p)
                    
        if not candidates:
            return self.get_base_platform_at(foot_x)
            
        candidates.sort(key=lambda p: p['y'])
        return candidates[0]

    def check_fullscreen_occlusion(self):
        """Si hay una ventana en pantalla completa sobre Gardevoir, colocarse detras."""
        _, fs_rects = self.monitor_mgr.scan()
        foot_x = self.x + self.ground_x
        foot_y = self.y + self.ground_y
        
        covered = False
        for r in fs_rects:
            if r['x1'] <= foot_x <= r['x2'] and r['y1'] <= foot_y <= r['y2']:
                covered = True
                break
                
        gdk_win = self.get_window()
        if covered and not self.is_behind_fullscreen:
            self.is_behind_fullscreen = True
            self.set_keep_above(False)
            if gdk_win:
                gdk_win.lower()
        elif not covered and self.is_behind_fullscreen:
            self.is_behind_fullscreen = False
            self.set_keep_above(True)
            if gdk_win:
                gdk_win.raise_()

    def play_sound(self, sound_name):
        if not self.sound_enabled:
            return
        path = os.path.join(SOUNDS_DIR, sound_name)
        if os.path.exists(path):
            try:
                subprocess.Popen(['pw-play', '--volume=0.35', path],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    def set_anim(self, anim_name):
        if anim_name in self.sprite_mgr.anims:
            self.current_anim = anim_name
            self.frame_idx = 0
            self.tick_counter = 0
            self.queue_draw()

    def set_state(self, state, timer=100):
        self.state = state
        self.state_timer = timer
        
        if state == 'WALK':
            self.set_anim('Walk')
        elif state == 'IDLE':
            self.set_anim('Idle')
        elif state == 'HOP':
            self.set_anim('Hop')
        elif state == 'ROTATE':
            self.set_anim('Rotate')
        elif state == 'SLEEP':
            self.set_anim('Sleep')
        elif state == 'APPEAL':
            self.set_anim('Appeal')
            self.play_sound('gardevoir-mega.ogg')
        elif state == 'ATTACK':
            self.set_anim('Attack')
            self.play_sound('shiny_sparkle.wav')
        elif state == 'DRAGGING':
            self.set_anim('Hop')
        elif state == 'FALLING':
            self.set_anim('Hurt')

    def on_tick(self):
        if self.is_dragging:
            return True

        self.check_fullscreen_occlusion()

        anim_data = self.sprite_mgr.anims.get(self.current_anim)
        if not anim_data:
            return True
            
        durations = anim_data['durations']
        cur_duration = durations[self.frame_idx % len(durations)]
        
        self.tick_counter += 1
        if self.tick_counter >= max(1, cur_duration // 2):
            self.tick_counter = 0
            self.frame_idx = (self.frame_idx + 1) % anim_data['cols']
            self.queue_draw()
            
            if self.frame_idx == 0:
                if self.state in ['HOP', 'ROTATE', 'APPEAL', 'ATTACK']:
                    self.set_state('IDLE', random.randint(45, 90))

        # FISICA: Caida hacia plataforma
        if self.state == 'FALLING':
            self.vy += 2.6
            self.y += self.vy
            
            target_plat = self.find_landing_platform(self.x + self.ground_x, self.y)
            if self.y >= target_plat['y']:
                self.y = target_plat['y']
                self.vy = 0.0
                self.current_platform = target_plat
                self.set_state('HOP')
                
            self.move(int(self.x), int(self.y))
            return True

        # COMPORTAMIENTO: Caminar (Multi-pantalla fluido)
        if self.state == 'WALK':
            speed = 2.7
            dx = speed if self.direction == DIR_RIGHT else -speed
            self.x += dx
            
            # Si esta en la base, puede transitar libremente entre monitores
            if 'monitor' in self.current_platform['name'] or 'base' in self.current_platform['name']:
                # Actualizar altura de suelo al cruzar de un monitor al otro
                cur_base = self.get_base_platform_at(self.x + self.ground_x)
                self.current_platform = cur_base
                min_x = self.total_min_x + 10
                max_x = self.total_max_x - 10
            else:
                min_x = self.current_platform['x1']
                max_x = self.current_platform['x2']
            
            # Limites y giro
            if self.direction == DIR_RIGHT and self.x >= max_x:
                self.x = max_x
                if not ('monitor' in self.current_platform['name'] or 'base' in self.current_platform['name']) and random.random() < 0.40:
                    self.direction = DIR_RIGHT
                    self.set_state('FALLING')
                    self.vy = 1.0
                else:
                    self.direction = DIR_LEFT
                    self.queue_draw()
            elif self.direction == DIR_LEFT and self.x <= min_x:
                self.x = min_x
                if not ('monitor' in self.current_platform['name'] or 'base' in self.current_platform['name']) and random.random() < 0.40:
                    self.direction = DIR_LEFT
                    self.set_state('FALLING')
                    self.vy = 1.0
                else:
                    self.direction = DIR_RIGHT
                    self.queue_draw()
                    
            self.y = self.current_platform['y']
            self.move(int(self.x), int(self.y))
            
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.set_state('IDLE', random.randint(40, 80))
                
        # COMPORTAMIENTO: Espera activa
        elif self.state == 'IDLE':
            self.y = self.current_platform['y']
            self.move(int(self.x), int(self.y))
            
            # Mirar a los lados mientras piensa
            if self.state_timer % 25 == 0:
                r_look = random.random()
                if r_look < 0.35:
                    self.direction = DIR_DOWN
                elif r_look < 0.65:
                    self.direction = DIR_RIGHT
                else:
                    self.direction = DIR_LEFT
                self.queue_draw()

            self.state_timer -= 1
            if self.state_timer <= 0:
                roll = random.random()
                if roll < 0.70: # Alta probabilidad de seguir caminando
                    # Si esta en monitor 0, incentivar caminar a la derecha (monitor 1)
                    if self.x < 1500:
                        self.direction = DIR_RIGHT if random.random() < 0.75 else DIR_LEFT
                    # Si esta en monitor 1, incentivar regresar al monitor 0
                    elif self.x > 2200:
                        self.direction = DIR_LEFT if random.random() < 0.75 else DIR_RIGHT
                    else:
                        self.direction = DIR_RIGHT if random.random() < 0.5 else DIR_LEFT
                        
                    self.set_state('WALK', random.randint(150, 320))
                elif roll < 0.85:
                    self.set_state('HOP')
                elif roll < 0.95:
                    self.set_state('ROTATE')
                else:
                    self.set_state('APPEAL')
                    
        elif self.state == 'SLEEP':
            self.y = self.current_platform['y']
            self.move(int(self.x), int(self.y))
            self.state_timer -= 1
            if self.state_timer <= 0:
                self.set_state('IDLE', 60)

        return True

    def on_draw(self, widget, cr):
        cr.set_operator(cairo.OPERATOR_CLEAR)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        
        anim_data = self.sprite_mgr.anims.get(self.current_anim)
        if not anim_data:
            return False
            
        row_dir = self.direction
        if anim_data['rows'] == 1:
            row_dir = 0
        elif row_dir not in anim_data['frames']:
            row_dir = 0
            
        frames = anim_data['frames'][row_dir]
        frame = frames[self.frame_idx % len(frames)]
        
        anchor_x, anchor_y = anim_data['anchor']
        draw_x = self.ground_x - int(anchor_x * self.scale)
        draw_y = self.ground_y - int(anchor_y * self.scale)
        
        Gdk.cairo_set_source_pixbuf(cr, frame, draw_x, draw_y)
        cr.paint()
        return False

    def on_button_press(self, widget, event):
        now = time.time()
        if event.button == 1:
            if now - self.last_click_time < 0.35:
                self.set_state('ATTACK')
                return
            self.last_click_time = now
            
            self.is_dragging = True
            self.drag_offset_x = event.x_root - self.x
            self.drag_offset_y = event.y_root - self.y
            self.set_state('DRAGGING')
            
        elif event.button == 3:
            self.show_context_menu(event)

    def on_motion_notify(self, widget, event):
        if self.is_dragging:
            self.x = event.x_root - self.drag_offset_x
            self.y = event.y_root - self.drag_offset_y
            self.move(int(self.x), int(self.y))

    def on_button_release(self, widget, event):
        if event.button == 1 and self.is_dragging:
            self.is_dragging = False
            
            foot_x = self.x + self.ground_x
            target_plat = self.find_landing_platform(foot_x, self.y)
            
            if self.y < target_plat['y'] - 10:
                self.vy = 0.0
                self.set_state('FALLING')
            else:
                self.y = target_plat['y']
                self.current_platform = target_plat
                self.move(int(self.x), int(self.y))
                
                r = random.random()
                if r < 0.45:
                    self.set_state('APPEAL')
                elif r < 0.75:
                    self.set_state('ROTATE')
                else:
                    self.set_state('HOP')

    def show_context_menu(self, event):
        menu = Gtk.Menu()
        
        item_appeal = Gtk.MenuItem(label="Pose / Saludo")
        item_appeal.connect("activate", lambda _: self.set_state('APPEAL'))
        menu.append(item_appeal)

        item_rotate = Gtk.MenuItem(label="Giro 360")
        item_rotate.connect("activate", lambda _: self.set_state('ROTATE'))
        menu.append(item_rotate)
        
        item_hop = Gtk.MenuItem(label="Saltito (Hop)")
        item_hop.connect("activate", lambda _: self.set_state('HOP'))
        menu.append(item_hop)
        
        item_walk = Gtk.MenuItem(label="Caminar")
        item_walk.connect("activate", lambda _: self.set_state('WALK', 240))
        menu.append(item_walk)

        item_sleep = Gtk.MenuItem(label="Dormir")
        item_sleep.connect("activate", lambda _: self.set_state('SLEEP', 600))
        menu.append(item_sleep)
        
        item_attack = Gtk.MenuItem(label="Ataque Psiquico")
        item_attack.connect("activate", lambda _: self.set_state('ATTACK'))
        menu.append(item_attack)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        scale_item = Gtk.MenuItem(label="Escala")
        scale_menu = Gtk.Menu()
        for s_val, s_label in [(1.5, "1.5x"), (2.0, "2.0x"), (2.5, "2.5x"), (3.0, "3.0x")]:
            mi = Gtk.MenuItem(label=s_label)
            mi.connect("activate", lambda _, s=s_val: self.change_scale(s))
            scale_menu.append(mi)
        scale_item.set_submenu(scale_menu)
        menu.append(scale_item)
        
        sound_item = Gtk.CheckMenuItem(label="Efectos de sonido")
        sound_item.set_active(self.sound_enabled)
        sound_item.connect("toggled", lambda w: setattr(self, 'sound_enabled', w.get_active()))
        menu.append(sound_item)
        
        menu.append(Gtk.SeparatorMenuItem())
        
        quit_item = Gtk.MenuItem(label="Cerrar")
        quit_item.connect("activate", lambda _: Gtk.main_quit())
        menu.append(quit_item)
        
        menu.show_all()
        menu.popup_at_pointer(event)

    def change_scale(self, new_scale):
        self.scale = new_scale
        self.sprite_mgr = SpriteManager(SPRITES_DIR, scale=self.scale)
        self.canvas_w = int(80 * self.scale)
        self.canvas_h = int(96 * self.scale)
        self.ground_x = self.canvas_w // 2
        self.ground_y = self.canvas_h - int(4 * self.scale)
        self.set_size_request(self.canvas_w, self.canvas_h)
        self.update_monitors_geometry()
        self.current_platform = self.find_landing_platform(self.x + self.ground_x, self.y)
        self.y = self.current_platform['y']
        self.move(int(self.x), int(self.y))
        self.queue_draw()

if __name__ == '__main__':
    scale = 2.0
    if len(sys.argv) > 1:
        try:
            scale = float(sys.argv[1])
        except ValueError:
            pass
            
    pet = GardevoirPet(scale=scale)
    Gtk.main()
