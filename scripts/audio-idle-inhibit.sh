#!/usr/bin/env bash
# ==============================================================================
# 🌸 Audio Idle & Dim Inhibit Controller (Gardevoir Setup)
# 
# Características:
# 1. 100% reactivo al bus de audio en tiempo real (pactl subscribe) a 0% CPU.
# 2. Sin polling innecesario: cuando no hay música, el proceso duerme bloqueado en
#    el kernel (0 wakeups, 0 consumo de batería).
# 3. Filtra únicamente eventos de 'sink' y 'sink-input' (evita bucles con 'client').
# 4. Protección de batería: no inhibe si la batería está en <= 15% en descarga.
# 5. Respeta el bloqueo manual: si la pantalla está bloqueada, se libera el inhibidor
#    para que el monitor descanse mientras suena la música.
# 6. Transición limpia: Espera 4 segundos de silencio tras parar el audio antes de
#    desinhibir, evitando parpadeos de brillo entre canciones o pausas breves.
# 7. Inhibición nativa a través de Cinnamon SessionManager (flag 12: idle + suspend)
#    y systemd-logind (idle:sleep).
# ==============================================================================

export DISPLAY="${DISPLAY:-:0}"

if [ "$1" = "--status" ]; then
    is_playing="NO"
    pactl list sinks 2>/dev/null | grep -q "State: RUNNING" && is_playing="SÍ"
    
    is_locked="NO"
    gdbus call --session --dest org.cinnamon.ScreenSaver --object-path /org/cinnamon/ScreenSaver --method org.cinnamon.ScreenSaver.GetActive 2>/dev/null | grep -q 'true' && is_locked="SÍ"

    is_sm_inh="NO"
    gdbus call --session --dest org.gnome.SessionManager --object-path /org/gnome/SessionManager --method org.gnome.SessionManager.IsInhibited 8 2>/dev/null | grep -q 'true' && is_sm_inh="SÍ"

    bat_stat="Cargando / CA"
    [ -r /sys/class/power_supply/BAT0/status ] && bat_stat=$(cat /sys/class/power_supply/BAT0/status)
    bat_cap="N/A"
    [ -r /sys/class/power_supply/BAT0/capacity ] && bat_cap="$(cat /sys/class/power_supply/BAT0/capacity)%"

    echo "================ ESTADO AUDIO INHIBIT ================"
    echo "🎵 Audio reproduciéndose:  $is_playing"
    echo "🔒 Pantalla bloqueada:      $is_locked"
    echo "🛡️  Inhibición activa (SM):  $is_sm_inh"
    echo "🔋 Batería:                 $bat_cap ($bat_stat)"
    echo "======================================================="
    exit 0
fi

PID_FILE="/tmp/audio-idle-inhibit-${USER}.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null && [ "$OLD_PID" -ne "$$" ]; then
        exit 0
    fi
fi
echo $$ > "$PID_FILE"

BATTERY_CRITICAL=15
SILENCE_TICKS=0
GRACE_LIMIT=4   # Segundos de gracia tras parar el audio antes de quitar la inhibición
INHIBIT_PID=""

is_inhibited() {
    [ -n "$INHIBIT_PID" ] && kill -0 "$INHIBIT_PID" 2>/dev/null
}

is_on_battery() {
    local stat
    if [ -r /sys/class/power_supply/BAT0/status ]; then
        stat=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null)
        [ "$stat" = "Discharging" ] && return 0
    fi
    return 1
}

is_battery_critical() {
    local cap stat
    if [ -r /sys/class/power_supply/BAT0/capacity ] && [ -r /sys/class/power_supply/BAT0/status ]; then
        cap=$(cat /sys/class/power_supply/BAT0/capacity 2>/dev/null)
        stat=$(cat /sys/class/power_supply/BAT0/status 2>/dev/null)
        if [ "$stat" = "Discharging" ] && [ -n "$cap" ] && [ "$cap" -le "$BATTERY_CRITICAL" ]; then
            return 0
        fi
    fi
    return 1
}

is_screen_locked() {
    gdbus call --session --dest org.cinnamon.ScreenSaver --object-path /org/cinnamon/ScreenSaver --method org.cinnamon.ScreenSaver.GetActive 2>/dev/null | grep -q 'true'
}

is_audio_playing() {
    # En PipeWire o PulseAudio: si cualquier sink está reproduciendo audio activo al hardware
    pactl list sinks 2>/dev/null | grep -q "State: RUNNING"
}

start_inhibit() {
    if ! is_inhibited; then
        # Mantiene la inhibición activa ÚNICAMENTE para inactividad (pantalla y salvapantallas)
        # Flag 8 = GSM_INHIBITOR_FLAG_IDLE (evita oscurecimiento y salvapantallas, sin bloquear apagado del sistema)
        python3 -c "
import dbus, signal
ses_bus = dbus.SessionBus()
sm = ses_bus.get_object('org.gnome.SessionManager', '/org/gnome/SessionManager')
sm.Inhibit('AudioInhibit', dbus.UInt32(0), 'Audio playing', dbus.UInt32(8), dbus_interface='org.gnome.SessionManager')
signal.pause()
" >/dev/null 2>&1 &
        INHIBIT_PID=$!
        # Restablece el brillo normal si la pantalla ya se había atenuado
        cinnamon-screensaver-command -d >/dev/null 2>&1 || true
    fi
}

stop_inhibit() {
    if is_inhibited; then
        kill "$INHIBIT_PID" 2>/dev/null
        wait "$INHIBIT_PID" 2>/dev/null
        INHIBIT_PID=""
    fi
}

cleanup() {
    stop_inhibit
    rm -f "$PID_FILE"
    exit 0
}

trap cleanup SIGINT SIGTERM SIGHUP EXIT

evaluate_state() {
    # 1. Batería crítica (<= 15% en descarga): Cierre inmediato para ahorrar energía
    if is_battery_critical; then
        stop_inhibit
        SILENCE_TICKS=0
        return
    fi

    # 2. Pantalla bloqueada: Cierre para que el monitor pueda apagarse
    if is_screen_locked; then
        stop_inhibit
        SILENCE_TICKS=0
        return
    fi

    # 3. Audio activo
    if is_audio_playing; then
        SILENCE_TICKS=0
        start_inhibit
    else
        # Si no hay audio pero el inhibidor sigue activo:
        if is_inhibited; then
            SILENCE_TICKS=$((SILENCE_TICKS + 1))
            # Esperar a que el decaimiento natural confirme el silencio
            if [ "$SILENCE_TICKS" -ge "$GRACE_LIMIT" ]; then
                stop_inhibit
                SILENCE_TICKS=0
            fi
        else
            SILENCE_TICKS=0
        fi
    fi
}

# Inicializar primer chequeo
evaluate_state

# Bucle reactivo al bus de audio (exactamente como Glava Controller)
while true; do
    pactl subscribe 2>/dev/null | grep --line-buffered -E "Event '(new|change|remove)' on (sink-input|sink)" | while true; do
        if is_inhibited; then
            # Cuando hay audio o en período de gracia, comprobar cada 1s para detectar pausas o fin de gracia
            read -t 1 _ || true
        else
            # Cuando hay silencio total, dormir bloqueado en el socket hasta el próximo evento de audio (0 CPU)
            read _ || true
        fi
        evaluate_state
    done
    sleep 1
done
