#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <X11/Xlib.h>
#include <X11/XKBlib.h>
#include <X11/keysym.h>
#include <X11/extensions/record.h>

// Tabla CP437 para códigos DOS/Windows 128..255
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
        KeySym keysym = XkbKeycodeToKeysym(ctrl_dpy, keycode, 0, 0);

        if (keysym == XK_Alt_L || keysym == XK_Alt_R || keysym == XK_Meta_L || keysym == XK_Meta_R) {
            if (type == KeyPress) {
                alt_held = 1;
                digit_val = 0;
                digit_count = 0;
                leading_zero = 0;
            } else if (type == KeyRelease) {
                if (alt_held && digit_count > 0) {
                    int codepoint = digit_val;
                    if (!leading_zero && digit_val >= 128 && digit_val <= 255) {
                        codepoint = cp437_table[digit_val - 128];
                    } else if (digit_val == 3) {
                        codepoint = 0x2665;
                    }
                    send_unicode(codepoint);
                }
                alt_held = 0;
                digit_val = 0;
                digit_count = 0;
                leading_zero = 0;
            }
        } else if (alt_held && type == KeyPress) {
            int digit = -1;
            if (keysym >= XK_KP_0 && keysym <= XK_KP_9) {
                digit = keysym - XK_KP_0;
            } else if (keysym >= XK_KP_Insert && keysym <= XK_KP_Page_Up) {
                switch (keysym) {
                    case XK_KP_Insert: digit = 0; break;
                    case XK_KP_End: digit = 1; break;
                    case XK_KP_Down: digit = 2; break;
                    case XK_KP_Page_Down: digit = 3; break;
                    case XK_KP_Left: digit = 4; break;
                    case XK_KP_Begin: digit = 5; break;
                    case XK_KP_Right: digit = 6; break;
                    case XK_KP_Home: digit = 7; break;
                    case XK_KP_Up: digit = 8; break;
                    case XK_KP_Page_Up: digit = 9; break;
                }
            } else if (keysym >= XK_0 && keysym <= XK_9) {
                digit = keysym - XK_0;
            }

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

int main() {
    ctrl_dpy = XOpenDisplay(NULL);
    Display *data_dpy = XOpenDisplay(NULL);

    if (!ctrl_dpy || !data_dpy) {
        fprintf(stderr, "altcode-daemon: Error abriendo display X11\n");
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
