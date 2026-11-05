#!/bin/bash
set -euo pipefail

TARGET_DIR="${HOME}/Descargas"

if [ ! -d "$TARGET_DIR" ]; then
    exit 0
fi

# Buscar elementos en Descargas que tengan más de 15 días de antigüedad tanto en modificación (mtime) como en creación/cambio (ctime).
# Se excluyen archivos ocultos y descargas temporales en curso (.crdownload, .part, .tmp).
COUNT=0
while IFS= read -r -d '' item; do
    echo "Enviando a la papelera (>15 días): $(basename "$item")"
    gio trash "$item"
    COUNT=$((COUNT + 1))
done < <(find "$TARGET_DIR" -mindepth 1 -maxdepth 1 \
    ! -name ".*" \
    ! -name "*.crdownload" \
    ! -name "*.part" \
    ! -name "*.tmp" \
    -mtime +15 -ctime +15 -print0)

if [ "$COUNT" -eq 0 ]; then
    echo "Descargas al día: no hay elementos con más de 15 días."
fi
