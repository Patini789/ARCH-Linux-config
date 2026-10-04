#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <X11/Xlib.h>
#include <X11/XKBlib.h>
#include <X11/keysym.h>
#include <X11/extensions/record.h>

// CP437 para códigos 1..31 (Alt+1 = ☺, Alt+3 = ♥, etc.)
static const int cp437_low_table[32] = {
    0x0000, 0x263A, 0x263B, 0x2665, 0x2666, 0x2663, 0x2660, 0x2022,
    0x25D8, 0x25CB, 0x25D9, 0x2642, 0x2640, 0x266A, 0x266B, 0x263C,
    0x25BA, 0x25C4, 0x2195, 0x203C, 0x00B6, 0x00A7, 0x25AC, 0x21A8,
    0x2191, 0x2193, 0x2192, 0x2190, 0x221F, 0x2194, 0x25B2, 0x25BC
};

// CP437 para códigos OEM/DOS 128..255 (Alt+164 = ñ, Alt+165 = Ñ, Alt+168 = ¿, etc.)
static const int cp437_table[128] = {
    0x00C7, 0x00FC, 0x00E9, 0x00E2, 0x00E4, 0x00E0, 0x00E5, 0x00E7,
    0x00EA, 0x00EB, 0x00E8, 0x00EF, 0x00EE, 0x00EC, 0x00C4, 0x00C5,
    0x00C9, 0x00E6, 0x00C6, 0x00F4, 0x00F6, 0x00F2, 0x00FB, 0x00F9,
    0x00FF, 0x00D6, 0x00DC, 0x00A2, 0x00A3, 0x00A5, 0x20A7, 0x0192,
    0x00E1, 0x00ED, 0x00F3, 0x00FA, 0x00F1, 0x00D1, 0x00AA, 0x00BA,
    0x00BF, 0x2310, 0x00AC, 0x00BD, 0x00BC, 0x00A1, 0x00AB, 0x00BB,
    0x2591, 0x2592, 0x2593, 0x2502, 0x2524, 0x2561, 0x2562, 0x2556,
    0x2557, 0x2563, 0x2551, 0x2557, 0x255D, 0x255C, 0x255B, 0x2510,
    0x2514, 0x2534, 0x252C, 0x251C, 0x2500, 0x253C, 0x255E, 0x255F,
    0x255A, 0x2554, 0x2569, 0x2566, 0x2560, 0x2550, 0x256C, 0x2567,
    0x2568, 0x2564, 0x2565, 0x2559, 0x2558, 0x2552, 0x2553, 0x256B,
    0x256A, 0x2518, 0x250C, 0x2588, 0x2584, 0x258C, 0x2590, 0x2580,
    0x03B1, 0x00DF, 0x0393, 0x03C0, 0x03A3, 0x03C3, 0x00B5, 0x03C4,
    0x03A6, 0x0398, 0x03A9, 0x03B4, 0x221E, 0x03C6, 0x03B5, 0x2229,
    0x2261, 0x00B1, 0x2265, 0x2264, 0x2320, 0x2321, 0x00F7, 0x2248,
    0x00B0, 0x2219, 0x00B7, 0x221A, 0x207F, 0x00B2, 0x25A0, 0x00A0
};

static int alt_held = 0;
static int digit_val = 0;
static int digit_count = 0;
static int leading_zero = 0;
static Display *ctrl_dpy = NULL;

static inline int is_alt_key(KeySym sym) {
    return (sym == XK_Alt_L || sym == XK_Alt_R ||
            sym == XK_Meta_L || sym == XK_Meta_R ||
            sym == XK_ISO_Level3_Shift || sym == XK_Mode_switch);
}

static inline int is_alt_event(Display *dpy, KeyCode keycode) {
    KeySym s0 = XkbKeycodeToKeysym(dpy, keycode, 0, 0);
    KeySym s1 = XkbKeycodeToKeysym(dpy, keycode, 0, 1);
    return is_alt_key(s0) || is_alt_key(s1);
}

static inline int get_digit(Display *dpy, KeyCode keycode) {
    KeySym s0 = XkbKeycodeToKeysym(dpy, keycode, 0, 0);
    KeySym s1 = XkbKeycodeToKeysym(dpy, keycode, 0, 1);

    KeySym syms[2] = { s0, s1 };
    for (int i = 0; i < 2; i++) {
        KeySym s = syms[i];
        if (s >= XK_0 && s <= XK_9) return (int)(s - XK_0);
        if (s >= XK_KP_0 && s <= XK_KP_9) return (int)(s - XK_KP_0);
        switch (s) {
            case XK_KP_Insert:    return 0;
            case XK_KP_End:       return 1;
            case XK_KP_Down:      return 2;
            case XK_KP_Next:      return 3;
            case XK_KP_Left:      return 4;
            case XK_KP_Begin:     return 5;
            case XK_KP_Right:     return 6;
            case XK_KP_Home:      return 7;
            case XK_KP_Up:        return 8;
            case XK_KP_Prior:     return 9;
            default: break;
        }
    }
    return -1;
}

void send_unicode(int codepoint) {
    if (codepoint <= 0) return;
    char utf8[8] = {0};
    if (codepoint <= 0x7F) {
        utf8[0] = (char)codepoint;
    } else if (codepoint <= 0x7FF) {
        utf8[0] = (char)(0xC0 | ((codepoint >> 6) & 0x1F));
        utf8[1] = (char)(0x80 | (codepoint & 0x3F));
    } else if (codepoint <= 0xFFFF) {
        utf8[0] = (char)(0xE0 | ((codepoint >> 12) & 0x0F));
        utf8[1] = (char)(0x80 | ((codepoint >> 6) & 0x3F));
        utf8[2] = (char)(0x80 | (codepoint & 0x3F));
    } else if (codepoint <= 0x10FFFF) {
        utf8[0] = (char)(0xF0 | ((codepoint >> 18) & 0x07));
        utf8[1] = (char)(0x80 | ((codepoint >> 12) & 0x3F));
        utf8[2] = (char)(0x80 | ((codepoint >> 6) & 0x3F));
        utf8[3] = (char)(0x80 | (codepoint & 0x3F));
    }

    pid_t pid = fork();
    if (pid == 0) {
        usleep(20000); // 20ms para liberar el modificador
        execlp("xdotool", "xdotool", "type", "--clearmodifiers", "--", utf8, NULL);
        _exit(0);
    }
}

void record_callback(XPointer closure, XRecordInterceptData *data) {
    if (data->category != XRecordFromServer) {
        XRecordFreeData(data);
        return;
    }

    unsigned char *event_data = data->data;
    int type = event_data[0] & 0x7F;
    KeyCode keycode = event_data[1];

    if (type == KeyPress || type == KeyRelease) {
        if (is_alt_event(ctrl_dpy, keycode)) {
            if (type == KeyPress) {
                alt_held = 1;
                digit_val = 0;
                digit_count = 0;
                leading_zero = 0;
            } else if (type == KeyRelease) {
                if (alt_held && digit_count > 0) {
                    int codepoint = digit_val;
                    if (!leading_zero && digit_val >= 1 && digit_val <= 31) {
                        codepoint = cp437_low_table[digit_val];
                    } else if (!leading_zero && digit_val >= 128 && digit_val <= 255) {
                        codepoint = cp437_table[digit_val - 128];
                    }
                    send_unicode(codepoint);
                }
                alt_held = 0;
                digit_val = 0;
                digit_count = 0;
                leading_zero = 0;
            }
        } else if (alt_held && type == KeyPress) {
            int digit = get_digit(ctrl_dpy, keycode);
            if (digit >= 0) {
                if (digit_count == 0 && digit == 0) {
                    leading_zero = 1;
                }
                digit_val = digit_val * 10 + digit;
                digit_count++;
            }
        }
    }

    XRecordFreeData(data);
}

int acquire_lock(void) {
    const char *runtime_dir = getenv("XDG_RUNTIME_DIR");
    char lock_path[256];
    if (runtime_dir && runtime_dir[0]) {
        snprintf(lock_path, sizeof(lock_path), "%s/altcode-daemon.lock", runtime_dir);
    } else {
        snprintf(lock_path, sizeof(lock_path), "/tmp/altcode-daemon-%d.lock", getuid());
    }
    int lock_fd = open(lock_path, O_CREAT | O_RDWR, 0600);
    if (lock_fd < 0) return 0;
    if (flock(lock_fd, LOCK_EX | LOCK_NB) != 0) {
        close(lock_fd);
        return 0;
    }
    return 1;
}

int main(int argc, char *argv[]) {
    // Si no se pide foreground explícito (-f / --foreground), daemonizar
    int foreground = 0;
    if (argc > 1 && (strcmp(argv[1], "-f") == 0 || strcmp(argv[1], "--foreground") == 0)) {
        foreground = 1;
    }

    if (!foreground) {
        if (fork() != 0) {
            exit(0);
        }
        setsid();
    }

    if (!acquire_lock()) {
        fprintf(stderr, "altcode-daemon: Ya hay otra instancia ejecutándose.\n");
        return 0;
    }

    Display *data_dpy = NULL;
    for (int retry = 0; retry < 15; retry++) {
        ctrl_dpy = XOpenDisplay(NULL);
        data_dpy = XOpenDisplay(NULL);
        if (ctrl_dpy && data_dpy) break;
        if (ctrl_dpy) { XCloseDisplay(ctrl_dpy); ctrl_dpy = NULL; }
        if (data_dpy) { XCloseDisplay(data_dpy); data_dpy = NULL; }
        sleep(1);
    }

    if (!ctrl_dpy || !data_dpy) {
        fprintf(stderr, "altcode-daemon: Error abriendo display X11 tras reintentos.\n");
        return 1;
    }

    XRecordRange *range = XRecordAllocRange();
    if (!range) return 1;

    range->device_events.first = KeyPress;
    range->device_events.last = KeyRelease;

    XRecordClientSpec spec = XRecordAllClients;
    XRecordContext context = XRecordCreateContext(ctrl_dpy, 0, &spec, 1, &range, 1);
    if (!context) return 1;

    XFree(range);
    XSync(ctrl_dpy, False);

    XRecordEnableContext(data_dpy, context, record_callback, NULL);

    XRecordFreeContext(ctrl_dpy, context);
    XCloseDisplay(data_dpy);
    XCloseDisplay(ctrl_dpy);
    return 0;
}
