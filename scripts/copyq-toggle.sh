#!/bin/bash
# Alternar ventana del historial de CopyQ de forma estable.
# `copyq toggle` se cierra a los ~500ms por close_on_unfocus,
# así que mostramos/ocultamos manualmente para que el historial
# se eleve y mantenga el foco (Comportamiento tipo Win+V).
if copyq visible 2>/dev/null | grep -q "true"; then
    copyq hide
else
    copyq show
fi
