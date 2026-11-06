// -*- mode: js; js-indent-level: 4; indent-tabs-mode: nil -*-
const Clutter = imports.gi.Clutter;
const Cinnamon = imports.gi.Cinnamon;
const Meta = imports.gi.Meta;
const Main = imports.ui.main;
const WorkspaceModule = imports.ui.workspace;

let origWorkspaceInit = null;
let origWorkspaceSelectMonitor = null;
let origWorkspaceOnKeyPress = null;
let origWorkspaceMonitorSelectIndex = null;
let origWorkspaceMonitorOnCloneActivated = null;

function init(metadata) {}

function enable() {
    let Workspace = WorkspaceModule.Workspace;
    let WorkspaceMonitor = WorkspaceModule.WorkspaceMonitor;

    // 1. Hook Workspace.prototype._init: Start Overview on the current active monitor
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

        // Determine current active monitor from pointer or focused window
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

    // 2. Hook Workspace.prototype.selectMonitor: Warps pointer on monitor selection
    if (!origWorkspaceSelectMonitor) {
        origWorkspaceSelectMonitor = Workspace.prototype.selectMonitor;
    }
    Workspace.prototype.selectMonitor = function(index) {
        this.currentMonitorIndex = index;
        let monActor = this._monitors[this.currentMonitorIndex];
        if (monActor) {
            if (monActor.isEmpty()) {
                try {
                    let mon = Main.layoutManager.monitors[this.currentMonitorIndex];
                    if (mon) {
                        let cx = Math.floor(mon.x + mon.width / 2);
                        let cy = Math.floor(mon.y + mon.height / 2);
                        global.set_pointer(cx, cy);
                    }
                } catch (e) {}
            } else {
                monActor.showActiveSelection();
            }
        }
    };

    // 3. Hook WorkspaceMonitor.prototype.selectIndex: Warps pointer to selected window
    if (!origWorkspaceMonitorSelectIndex) {
        origWorkspaceMonitorSelectIndex = WorkspaceMonitor.prototype.selectIndex;
    }
    WorkspaceMonitor.prototype.selectIndex = function(index) {
        this._kbWindowIndex = index;
        let activeClone = null;
        if (index > -1 && index < this._windows.length) {
            activeClone = this._windows[this._kbWindowIndex];
            if (activeClone && activeClone.metaWindow) {
                try {
                    let rect = activeClone.metaWindow.get_frame_rect();
                    let cx = Math.floor(rect.x + rect.width / 2);
                    let cy = Math.floor(rect.y + rect.height / 2);
                    global.set_pointer(cx, cy);
                } catch (e) {}
            }
        }
        this._myWorkspace.selectActiveClone(activeClone, this);
    };

    // 4. Hook WorkspaceMonitor.prototype._onCloneActivated: Ensures focus and pointer alignment on activation
    if (!origWorkspaceMonitorOnCloneActivated) {
        origWorkspaceMonitorOnCloneActivated = WorkspaceMonitor.prototype._onCloneActivated;
    }
    WorkspaceMonitor.prototype._onCloneActivated = function(clone, time) {
        let wsIndex = undefined;
        if (this.metaWorkspace)
            wsIndex = this.metaWorkspace.index();

        if (clone && clone.metaWindow) {
            try {
                let rect = clone.metaWindow.get_frame_rect();
                let cx = Math.floor(rect.x + rect.width / 2);
                let cy = Math.floor(rect.y + rect.height / 2);
                global.set_pointer(cx, cy);
            } catch (e) {}
        }
        Main.activateWindow(clone.metaWindow, time, wsIndex);
    };

    // 5. Hook Workspace.prototype._onKeyPress: Seamless multi-monitor 2D boundary crossing & controls
    if (!origWorkspaceOnKeyPress) {
        origWorkspaceOnKeyPress = Workspace.prototype._onKeyPress;
    }
    Workspace.prototype._onKeyPress = function(actor, event) {
        let modifiers = Cinnamon.get_event_state(event);
        let symbol = event.get_key_symbol();
        let keycode = event.get_key_code();
        let ctrlAltMask = Clutter.ModifierType.CONTROL_MASK | Clutter.ModifierType.MOD1_MASK;
        let action = global.display.get_keybinding_action(keycode, modifiers);

        // Sort monitors left-to-right by horizontal X offset
        let monitors = Main.layoutManager.monitors;
        let sortedIndices = monitors.map((m, idx) => ({ idx, x: m.x }))
                                    .sort((a, b) => a.x - b.x)
                                    .map(m => m.idx);
        let posInSorted = sortedIndices.indexOf(this.currentMonitorIndex);
        if (posInSorted === -1) posInSorted = 0;

        // Tab / Shift+Tab: cycle non-empty monitors
        if ((symbol === Clutter.KEY_ISO_Left_Tab || symbol === Clutter.KEY_Tab) && !(modifiers & ctrlAltMask)) {
            let increment = symbol === Clutter.KEY_ISO_Left_Tab ? -1 : 1;
            this.selectNextNonEmptyMonitor(this.currentMonitorIndex, increment);
            return true;
        }

        // 'w' or 'W' (without modifiers): cycle monitors
        if ((symbol === Clutter.KEY_w || symbol === Clutter.KEY_W) &&
            !(modifiers & (Clutter.ModifierType.CONTROL_MASK | Clutter.ModifierType.MOD1_MASK | Clutter.ModifierType.MOD4_MASK))) {
            this.selectNextNonEmptyMonitor(this.currentMonitorIndex, 1);
            return true;
        }

        let activeMonitor = this._monitors[this.currentMonitorIndex];

        // Alt+M or Alt+Space: Context menu
        if ((symbol === Clutter.KEY_m || symbol === Clutter.KEY_M || symbol === Clutter.KEY_space) &&
            (modifiers & Clutter.ModifierType.MOD1_MASK) && !(modifiers & Clutter.ModifierType.CONTROL_MASK)) {
            if (activeMonitor) activeMonitor.showMenuForSelectedWindow();
            return true;
        }

        // Close window: Ctrl+W or Meta.KeyBindingAction.CLOSE
        if (action === Meta.KeyBindingAction.CLOSE ||
            (symbol === Clutter.KEY_w && (modifiers & Clutter.ModifierType.CONTROL_MASK))) {
            if (activeMonitor) activeMonitor.closeSelectedWindow();
            return true;
        }

        // Ctrl+M: Move window to next monitor
        if ((symbol === Clutter.KEY_m || symbol === Clutter.KEY_M) && (modifiers & Clutter.ModifierType.CONTROL_MASK)) {
            if (activeMonitor) activeMonitor.moveSelectedWindowToNextMonitor();
            return true;
        }

        // Return / Enter / Space: Activate selected window
        if (symbol === Clutter.KEY_Return || symbol === Clutter.KEY_KP_Enter || symbol === Clutter.KEY_space) {
            if (activeMonitor && activeMonitor.activateSelectedWindow()) {
                return true;
            }
            Main.overview.hide();
            return true;
        }

        // Escape: Exit overview
        if (symbol === Clutter.KEY_Escape) {
            Main.overview.hide();
            return true;
        }

        if (modifiers & ctrlAltMask) {
            return false;
        }

        // Multi-monitor arrow navigation
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
                    // Cross right to adjacent monitor
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
                    // Cross left to adjacent monitor
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
    let WorkspaceMonitor = WorkspaceModule.WorkspaceMonitor;

    if (origWorkspaceInit) {
        Workspace.prototype._init = origWorkspaceInit;
        origWorkspaceInit = null;
    }
    if (origWorkspaceSelectMonitor) {
        Workspace.prototype.selectMonitor = origWorkspaceSelectMonitor;
        origWorkspaceSelectMonitor = null;
    }
    if (origWorkspaceOnKeyPress) {
        Workspace.prototype._onKeyPress = origWorkspaceOnKeyPress;
        origWorkspaceOnKeyPress = null;
    }
    if (origWorkspaceMonitorSelectIndex) {
        WorkspaceMonitor.prototype.selectIndex = origWorkspaceMonitorSelectIndex;
        origWorkspaceMonitorSelectIndex = null;
    }
    if (origWorkspaceMonitorOnCloneActivated) {
        WorkspaceMonitor.prototype._onCloneActivated = origWorkspaceMonitorOnCloneActivated;
        origWorkspaceMonitorOnCloneActivated = null;
    }
}
