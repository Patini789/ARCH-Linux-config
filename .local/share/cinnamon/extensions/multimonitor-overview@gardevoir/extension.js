// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Clutter = imports.gi.Clutter;
const Cinnamon = imports.gi.Cinnamon;
const Meta = imports.gi.Meta;
const Main = imports.ui.main;
const WorkspaceModule = imports.ui.workspace;

let origWorkspaceInit = null;
let origWorkspaceOnKeyPress = null;

function init(metadata) {}

function enable() {
    let Workspace = WorkspaceModule.Workspace;
    let WorkspaceMonitor = WorkspaceModule.WorkspaceMonitor;

    // 1. Hook Workspace.prototype._init:
    // Abre el Overview directamente en el monitor donde está trabajando el usuario
    // (en lugar de forzar siempre el monitor primario), y preselecciona la ventana en foco.
    if (!origWorkspaceInit) {
        origWorkspaceInit = Workspace.prototype._init;
    }
    Workspace.prototype._init = function(metaWorkspace, view) {
        this.metaWorkspace = metaWorkspace;
        this.myView = view;
        this.actor = new Clutter.Group();
        this.actor.set_size(0, 0);
        this._monitors = [];
        this._activeClone = null;

        // Determinar el monitor activo desde la ventana con foco o la posición actual
        let targetMon = global.display.get_current_monitor();
        let fw = global.display.focus_window;
        if (fw) {
            let fwMon = fw.get_monitor();
            if (fwMon >= 0 && fwMon < Main.layoutManager.monitors.length) {
                targetMon = fwMon;
            }
        }
        this.currentMonitorIndex = targetMon;

        Main.layoutManager.monitors.forEach((monitor, ix) => {
            let m = new WorkspaceMonitor(metaWorkspace, ix, this);
            m.setGeometry(monitor.x, monitor.y, monitor.width, monitor.height, monitor.width * 0.01);
            this._monitors.push(m);
            this.actor.add_actor(m.actor);
        });

        // Mantener el monitor del usuario en vez de forzar salto al primario
        this.connect('focus-refresh-required', () => {
            let curMon = this._monitors[this.currentMonitorIndex];
            if (curMon && !curMon.isEmpty()) {
                if (fw) {
                    for (let i = 0; i < curMon._windows.length; i++) {
                        if (curMon._windows[i].metaWindow === fw) {
                            curMon._kbWindowIndex = i;
                            break;
                        }
                    }
                }
                this.selectMonitor(this.currentMonitorIndex);
            } else {
                this.selectNextNonEmptyMonitor(this.currentMonitorIndex - 1, 1);
            }
        });
    };

    // 2. Hook Workspace.prototype._onKeyPress:
    // Navegación bidimensional fluida entre monitores con flechas (cruce de bordes),
    // Down/Up en columna fija y ciclo con Tab / W (SIN mover el cursor del mouse).
    if (!origWorkspaceOnKeyPress) {
        origWorkspaceOnKeyPress = Workspace.prototype._onKeyPress;
    }
    Workspace.prototype._onKeyPress = function(actor, event) {
        let modifiers = Cinnamon.get_event_state(event);
        let symbol = event.get_key_symbol();
        let keycode = event.get_key_code();
        let ctrlAltMask = Clutter.ModifierType.CONTROL_MASK | Clutter.ModifierType.MOD1_MASK;
        let action = global.display.get_keybinding_action(keycode, modifiers);

        // Ordenar monitores de izquierda a derecha según su posición horizontal X
        let monitors = Main.layoutManager.monitors;
        let sortedIndices = monitors.map((m, idx) => ({ idx, x: m.x }))
                                    .sort((a, b) => a.x - b.x)
                                    .map(m => m.idx);
        let posInSorted = sortedIndices.indexOf(this.currentMonitorIndex);
        if (posInSorted === -1) posInSorted = 0;

        // Tab / Shift+Tab: ciclar entre monitores con ventanas
        if ((symbol === Clutter.KEY_ISO_Left_Tab || symbol === Clutter.KEY_Tab) && !(modifiers & ctrlAltMask)) {
            let increment = symbol === Clutter.KEY_ISO_Left_Tab ? -1 : 1;
            this.selectNextNonEmptyMonitor(this.currentMonitorIndex, increment);
            return true;
        }

        // 'w' o 'W' (sin modificadores): ciclar monitores
        if ((symbol === Clutter.KEY_w || symbol === Clutter.KEY_W) &&
            !(modifiers & (Clutter.ModifierType.CONTROL_MASK | Clutter.ModifierType.MOD1_MASK | Clutter.ModifierType.MOD4_MASK))) {
            this.selectNextNonEmptyMonitor(this.currentMonitorIndex, 1);
            return true;
        }

        let activeMonitor = this._monitors[this.currentMonitorIndex];

        // Alt+M o Alt+Space: menú contextual
        if ((symbol === Clutter.KEY_m || symbol === Clutter.KEY_M || symbol === Clutter.KEY_space) &&
            (modifiers & Clutter.ModifierType.MOD1_MASK) && !(modifiers & Clutter.ModifierType.CONTROL_MASK)) {
            if (activeMonitor) activeMonitor.showMenuForSelectedWindow();
            return true;
        }

        // Cerrar ventana: Ctrl+W o acción CLOSE
        if (action === Meta.KeyBindingAction.CLOSE ||
            (symbol === Clutter.KEY_w && (modifiers & Clutter.ModifierType.CONTROL_MASK))) {
            if (activeMonitor) activeMonitor.closeSelectedWindow();
            return true;
        }

        // Ctrl+M: mover ventana al siguiente monitor
        if ((symbol === Clutter.KEY_m || symbol === Clutter.KEY_M) && (modifiers & Clutter.ModifierType.CONTROL_MASK)) {
            if (activeMonitor) activeMonitor.moveSelectedWindowToNextMonitor();
            return true;
        }

        // Return / Enter / Espacio: activar ventana seleccionada
        if (symbol === Clutter.KEY_Return || symbol === Clutter.KEY_KP_Enter || symbol === Clutter.KEY_space) {
            if (activeMonitor && activeMonitor.activateSelectedWindow()) {
                return true;
            }
            Main.overview.hide();
            return true;
        }

        // Escape: salir de Overview
        if (symbol === Clutter.KEY_Escape) {
            Main.overview.hide();
            return true;
        }

        if (modifiers & ctrlAltMask) {
            return false;
        }

        // Navegación con flechas
        let isArrow = (symbol === Clutter.KEY_Right || symbol === Clutter.KEY_Left ||
                       symbol === Clutter.KEY_Down || symbol === Clutter.KEY_Up);

        if (isArrow && activeMonitor) {
            let numWindows = activeMonitor._windows.length;
            let curIdx = activeMonitor._kbWindowIndex;

            if (numWindows === 0) {
                if (symbol === Clutter.KEY_Right) {
                    let nextIdx = sortedIndices[(posInSorted + 1) % sortedIndices.length];
                    this.selectMonitor(nextIdx);
                    return true;
                } else if (symbol === Clutter.KEY_Left) {
                    let prevIdx = sortedIndices[(posInSorted - 1 + sortedIndices.length) % sortedIndices.length];
                    this.selectMonitor(prevIdx);
                    return true;
                }
                return false;
            }

            let numCols = Math.ceil(Math.sqrt(numWindows));
            let numRows = Math.ceil(numWindows / numCols);
            let curRow = Math.floor(curIdx / numCols);
            let curCol = curIdx % numCols;

            if (symbol === Clutter.KEY_Right) {
                if (curCol < numCols - 1 && (curIdx + 1) < numWindows) {
                    activeMonitor.selectIndex(curIdx + 1);
                    return true;
                } else {
                    // Cruce hacia el monitor adyacente a la derecha
                    let nextIdx = sortedIndices[(posInSorted + 1) % sortedIndices.length];
                    this.selectMonitor(nextIdx);
                    let targetMon = this._monitors[nextIdx];
                    if (targetMon && targetMon._windows.length > 0) {
                        let tCols = Math.ceil(Math.sqrt(targetMon._windows.length));
                        let targetWin = Math.min(targetMon._windows.length - 1, curRow * tCols);
                        targetMon.selectIndex(Math.max(0, targetWin));
                    }
                    return true;
                }
            } else if (symbol === Clutter.KEY_Left) {
                if (curCol > 0) {
                    activeMonitor.selectIndex(curIdx - 1);
                    return true;
                } else {
                    // Cruce hacia el monitor adyacente a la izquierda
                    let prevIdx = sortedIndices[(posInSorted - 1 + sortedIndices.length) % sortedIndices.length];
                    this.selectMonitor(prevIdx);
                    let targetMon = this._monitors[prevIdx];
                    if (targetMon && targetMon._windows.length > 0) {
                        let tCols = Math.ceil(Math.sqrt(targetMon._windows.length));
                        let targetWin = Math.min(targetMon._windows.length - 1, curRow * tCols + (tCols - 1));
                        targetMon.selectIndex(Math.max(0, targetWin));
                    }
                    return true;
                }
            } else if (symbol === Clutter.KEY_Down) {
                if (curRow < numRows - 1) {
                    let targetWin = (curRow + 1) * numCols + curCol;
                    if (targetWin >= numWindows) targetWin = numWindows - 1;
                    activeMonitor.selectIndex(targetWin);
                } else {
                    let targetWin = curCol;
                    if (targetWin >= numWindows) targetWin = numWindows - 1;
                    activeMonitor.selectIndex(targetWin);
                }
                return true;
            } else if (symbol === Clutter.KEY_Up) {
                if (curRow > 0) {
                    let targetWin = (curRow - 1) * numCols + curCol;
                    activeMonitor.selectIndex(targetWin);
                } else {
                    let targetWin = (numRows - 1) * numCols + curCol;
                    if (targetWin >= numWindows) targetWin = (numRows - 2) * numCols + curCol;
                    if (targetWin < 0) targetWin = 0;
                    activeMonitor.selectIndex(Math.min(numWindows - 1, targetWin));
                }
                return true;
            }
        }

        return false;
    };
}

function disable() {
    let Workspace = WorkspaceModule.Workspace;

    if (origWorkspaceInit) {
        Workspace.prototype._init = origWorkspaceInit;
        origWorkspaceInit = null;
    }
    if (origWorkspaceOnKeyPress) {
        Workspace.prototype._onKeyPress = origWorkspaceOnKeyPress;
        origWorkspaceOnKeyPress = null;
    }
}
