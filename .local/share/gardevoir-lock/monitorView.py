#!/usr/bin/python3

from gi.repository import Gtk, Gio, GLib, GObject
import re
import cairo
import signal
import random
import time
import math

import status
from baseWindow import BaseWindow
from util import settings, utils, trackers

class WallpaperStack(Gtk.Stack):
    """
    WallpaperStack implements a crossfade when changing backgrounds.

    An initial image is made and added to the GtkStack.  When a new
    image is requested, it is created and added to the stack, then
    a crossfade transition is made to the new child.  The former
    visible stack child is then destroyed.  And this repeats.
    """
    def __init__(self):
        super(WallpaperStack, self).__init__()

        self.set_transition_type(Gtk.StackTransitionType.NONE)
        self.set_transition_duration(1000)

        self.initialized = False
        self.current = None
        self.queued = None

        # ---- Constelaciones Gardevoir Shiny ----
        self.particles = []
        self.last_tick = time.time()
        self.particle_w = 0
        self.particle_h = 0
        self.tick_id = 0

        trackers.con_tracker_get().connect(self, "destroy", self.on_constellations_destroy)
        self.tick_id = GLib.timeout_add(16, self.tick_constellations)

    def transition_to_image(self, image):
        """
        Queues a new image in the stack, and begins the transition to it.
        """
        self.queued = image
        self.queued.set_visible(True)

        trackers.con_tracker_get().connect_after(image,
                                                 "draw",
                                                 self.shade_wallpaper)

        self.add(self.queued)

        if not self.initialized:
            self.visible_image_changed()
            self.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            self.initialized = True
            return

        self.set_visible_child(self.queued)
        GObject.timeout_add(2000, self.visible_image_changed)

    def visible_image_changed(self, data=None):
        if self.current is not None:
            tmp = self.current

            self.remove(tmp)
            tmp.destroy()

        self.current = self.queued
        self.queued = None

        return False

    def shade_wallpaper(self, widget, cr):
        """
        This draw callback adds a shade mask over the current
        image.  It is uniform when not Awake, and acquires a
        significant gradient vertically framing the unlock dialog
        when Awake.

        Encima de la sombra se dibuja las constelaciones.
        """
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.7)
        cr.paint()

        alloc = widget.get_allocation()
        if alloc.width > 0 and alloc.height > 0:
            if not self.particles:
                self.spawn_particles(alloc.width, alloc.height)
            self.draw_constellations(cr, alloc.width, alloc.height)
        return False

    def on_constellations_destroy(self, widget, data=None):
        self.remove_tick()

    def remove_tick(self):
        if self.tick_id:
            GLib.source_remove(self.tick_id)
            self.tick_id = 0

    def spawn_particles(self, width, height):
        self.particles = []
        self.particle_w = width
        self.particle_h = height
        count = min(45, int((width * height) / 32000))
        if count < 20:
            count = 20
        for _ in range(count):
            self.particles.append({
                'x': random.random() * width,
                'y': random.random() * height,
                'size': random.random() * 2.1 + 0.9,
                'speed_x': (random.random() - 0.5) * 28.0,
                'speed_y': -(random.random() * 16.0 + 5.0),
                'alpha': random.random() * 0.55 + 0.3,
                'shiny': random.random() > 0.87,
                'pulse': random.random() * math.pi * 2,
                'pulse_speed': random.random() * 1.6 + 0.8,
            })

    def tick_constellations(self, data=None):
        try:
            # Sin animación cuando no hay nadie desbloqueando (duerme)
            if not status.Awake:
                return True

            now = time.time()
            dt = min(0.15, now - self.last_tick)
            self.last_tick = now

            for p in self.particles:
                p['x'] += p['speed_x'] * dt
                p['y'] += p['speed_y'] * dt
                p['pulse'] += p['pulse_speed'] * dt

                w = self.particle_w
                h = self.particle_h
                if p['y'] < -12:
                    p['y'] = h + 12
                    p['x'] = random.random() * w
                if p['x'] < -12:
                    p['x'] = w + 12
                if p['x'] > w + 12:
                    p['x'] = -12

            self.queue_draw()
            return True
        except Exception:
            import traceback, sys
            print("constellations tick error:", file=sys.stderr)
            traceback.print_exc()
            self.remove_tick()
            return False

    def draw_star(self, cr, cx, cy, outer, inner):
        rot = math.pi / 2 * 3
        step = math.pi / 4
        for _ in range(4):
            cr.line_to(cx + math.cos(rot) * outer, cy + math.sin(rot) * outer)
            rot += step
            cr.line_to(cx + math.cos(rot) * inner, cy + math.sin(rot) * inner)
            rot += step
        cr.close_path()

    def draw_constellations(self, cr, width, height):
        # Conexiones tipo constelación (cyán)
        max_dist = 140
        for i in range(len(self.particles)):
            for j in range(i + 1, len(self.particles)):
                a = self.particles[i]
                b = self.particles[j]
                dx = a['x'] - b['x']
                dy = a['y'] - b['y']
                dist = math.sqrt(dx * dx + dy * dy)
                if dist < max_dist:
                    alpha = (1 - dist / max_dist) * 0.28
                    cr.set_source_rgba(0.45, 0.87, 1.0, alpha)
                    cr.set_line_width(0.9)
                    cr.move_to(a['x'], a['y'])
                    cr.line_to(b['x'], b['y'])
                    cr.stroke()

        for p in self.particles:
            pulse_alpha = max(0.15, p['alpha'] + math.sin(p['pulse']) * 0.3)
            cx = p['x']
            cy = p['y']

            if p['shiny']:
                grad = cairo.RadialGradient(cx, cy, 0, cx, cy, p['size'] * 4.0)
                grad.add_color_stop_rgba(0.0, 1.0, 0.45, 0.68, 0.5 * pulse_alpha)
                grad.add_color_stop_rgba(1.0, 1.0, 0.45, 0.68, 0.0)
                cr.set_source(grad)
                cr.arc(cx, cy, p['size'] * 4.0, 0, math.pi * 2)
                cr.fill()

                cr.set_source_rgba(1.0, 0.55, 0.77, pulse_alpha)
                cr.save()
                cr.translate(cx, cy)
                cr.rotate(p['pulse'] * 0.4)
                cr.move_to(0, 0)
                self.draw_star(cr, 0, 0, p['size'] * 2.2, p['size'] * 0.85)
                cr.fill()
                cr.restore()
            else:
                grad = cairo.RadialGradient(cx, cy, 0, cx, cy, p['size'] * 3.2)
                grad.add_color_stop_rgba(0, 0.45, 0.87, 1.0, pulse_alpha * 0.6)
                grad.add_color_stop_rgba(1, 0.45, 0.87, 1.0, 0.0)
                cr.set_source(grad)
                cr.arc(cx, cy, p['size'] * 3.2, 0, math.pi * 2)
                cr.fill()

                cr.set_source_rgba(0.45, 0.87, 1.0, pulse_alpha)
                cr.arc(cx, cy, p['size'], 0, math.pi * 2)
                cr.fill()

class MonitorView(BaseWindow):
    """
    A monitor-sized child of the stage that is responsible for displaying
    the currently-selected wallpaper or appropriate plug-in.
    """
    def __init__(self, index):
        super(MonitorView, self).__init__()

        self.monitor_index = index

        self.update_geometry()

        self.wallpaper_stack = WallpaperStack()
        self.wallpaper_stack.show()
        self.wallpaper_stack.set_halign(Gtk.Align.FILL)
        self.wallpaper_stack.set_valign(Gtk.Align.FILL)
        self.add(self.wallpaper_stack)

        self.show_all()

    def set_next_wallpaper_image(self, image):
        self.wallpaper_stack.transition_to_image(image)
