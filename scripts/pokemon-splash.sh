#!/bin/bash

CACHE_FILE="/tmp/current_pokemon_logo.txt"
SOUND_FILE="/tmp/current_pokemon_sound.txt"

# 1. Reproducir sonido previo en segundo plano absoluto (0.001s, no bloqueante)
if [ -s "$SOUND_FILE" ]; then
    SOUND=$(cat "$SOUND_FILE")
    [ -f "$SOUND" ] && ( pw-play --volume=0.40 "$SOUND" &>/dev/null & )
fi

# 2. Mostrar el logo inmediatamente (ultra rápido)
if [ -s "$CACHE_FILE" ]; then
    fastfetch --logo "$CACHE_FILE" --logo-type file-raw 2>/dev/null
else
    pokemon-colorscripts -n "gardevoir" --no-title > "$CACHE_FILE" 2>/dev/null
    echo "${HOME}/.local/share/sounds/pokemon/gardevoir.ogg" > "$SOUND_FILE"
    fastfetch --logo "$CACHE_FILE" --logo-type file-raw 2>/dev/null
fi

# 3. Generar en SEGUNDO PLANO el siguiente Pokémon y su sonido (CERO DELAY)
(
    ROLL=$(( RANDOM % 100 ))
    IS_SHINY=""
    NEXT_SOUND="${HOME}/.local/share/sounds/pokemon/gardevoir.ogg"

    if [ $ROLL -lt 50 ]; then
        POKE="gardevoir"
        if [ $(( RANDOM % 2 )) -eq 0 ]; then
            IS_SHINY="-s"
            NEXT_SOUND="${HOME}/.local/share/sounds/pokemon/shiny_sparkle.wav"
        fi
        pokemon-colorscripts -n "$POKE" $IS_SHINY --no-title > "$CACHE_FILE" 2>/dev/null
    elif [ $ROLL -lt 85 ]; then
        EVO_LIST=("ralts" "kirlia" "gallade")
        POKE="${EVO_LIST[$(( RANDOM % ${#EVO_LIST[@]} ))]}"
        if [ $(( RANDOM % 2 )) -eq 0 ]; then
            IS_SHINY="-s"
            NEXT_SOUND="${HOME}/.local/share/sounds/pokemon/shiny_sparkle.wav"
        fi
        pokemon-colorscripts -n "$POKE" $IS_SHINY --no-title > "$CACHE_FILE" 2>/dev/null
    else
        if [ $(( RANDOM % 8 )) -eq 0 ]; then
            IS_SHINY="-s"
            NEXT_SOUND="${HOME}/.local/share/sounds/pokemon/shiny_sparkle.wav"
        fi
        pokemon-colorscripts -r $IS_SHINY --no-title > "$CACHE_FILE" 2>/dev/null
    fi

    echo "$NEXT_SOUND" > "$SOUND_FILE"
) &>/dev/null &
