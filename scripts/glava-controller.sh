#!/usr/bin/env bash
# ==============================================================================
# 🌸 GLava Intelligent Audio & Power Controller (Gardevoir Setup)
# 
# Características:
# 1. Escucha en tiempo real los eventos del bus de audio (pactl subscribe) a 0% CPU.
# 2. Cierre DEFINITIVO si la batería está en <= 30% en descarga, en pantalla completa o bloqueada.
# 3. Tasa adaptativa inteligente: 30 FPS en batería para mínimo consumo, 60 FPS conectado a la corriente.
# 4. Transición limpia: Espera 3 segundos de silencio para que las barras caigan a cero
#    de forma natural antes de cerrar el proceso, eliminando barras congeladas o superpuestas.
# 5. Detección nativa universal (PipeWire y PulseAudio) a través del estado de los sinks.
# ==============================================================================

export DISPLAY="${DISPLAY:-:0}"

PID_FILE="/tmp/glava-controller-${USER}.pid"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null && [ "$OLD_PID" -ne "$$" ]; then
        exit 0
    fi
fi
echo $$ > "$PID_FILE"

BATTERY_CRITICAL=30
SILENCE_TICKS=0
GRACE_LIMIT=3   # Segundos de gracia tras parar el audio antes de cerrar GLava
CURRENT_FPS=60

is_glava_running() {
    pgrep -x glava >/dev/null 2>&1
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

is_fullscreen() {
    local active_win
    active_win=$(xdotool getactivewindow 2>/dev/null) || return 1
    xprop -id "$active_win" _NET_WM_STATE 2>/dev/null | grep -q "_NET_WM_STATE_FULLSCREEN"
}

start_glava() {
    local target_fps="${1:-60}"
    if ! is_glava_running; then
        nohup glava --desktop -r "setframerate $target_fps" >/dev/null 2>&1 &
        sleep 0.4
    fi
}

stop_glava() {
    if is_glava_running; then
        killall glava 2>/dev/null
        ( sleep 0.5; killall -9 glava 2>/dev/null ) &
    fi
}

cleanup() {
    stop_glava
    rm -f "$PID_FILE"
    exit 0
}

trap cleanup SIGINT SIGTERM SIGHUP EXIT

sleep 1

evaluate_state() {
    # 1. Batería baja (<= 30% en descarga): Cierre inmediato para ahorrar energía
    if is_battery_critical; then
        stop_glava
        SILENCE_TICKS=0
        return
    fi

    # 2. Pantalla completa o Pantalla bloqueada: Cierre para no gastar GPU a ciegas
    if is_fullscreen || is_screen_locked; then
        stop_glava
        SILENCE_TICKS=0
        return
    fi

    # 3. Audio activo
    if is_audio_playing; then
        SILENCE_TICKS=0
        local target_fps=60
        if is_on_battery; then
            target_fps=30
        fi

        if ! is_glava_running; then
            CURRENT_FPS="$target_fps"
            start_glava "$target_fps"
        elif [ "$CURRENT_FPS" != "$target_fps" ]; then
            # Si se conectó/desconectó el cargador mientras sonaba música, adaptar FPS
            CURRENT_FPS="$target_fps"
            killall glava 2>/dev/null
            sleep 0.2
            start_glava "$target_fps"
        fi
    else
        # Si no hay audio pero GLava sigue corriendo:
        if is_glava_running; then
            SILENCE_TICKS=$((SILENCE_TICKS + 1))
            # Esperar a que el decaimiento natural de audio baje las barras a cero
            if [ "$SILENCE_TICKS" -ge "$GRACE_LIMIT" ]; then
                stop_glava
                SILENCE_TICKS=0
            fi
        else
            SILENCE_TICKS=0
        fi
    fi
}

# Inicializar primer chequeo
evaluate_state

# Bucle reactivo al bus de audio con tick de 1 segundo para verificar silencio, bloqueo y fullscreen
while true; do
    pactl subscribe 2>/dev/null | grep --line-buffered -E "Event '(new|change|remove)' on (sink-input|sink)" | while true; do
        read -t 1 _ || true
        evaluate_state
    done
    sleep 1
done
