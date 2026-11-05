#!/bin/bash
gpu=""
mem_used=""
mem_total=""

# 1. Detección nativa para AMD Radeon (vía sysfs del kernel sin sobrecarga de CPU)
for p in /sys/class/drm/card*/device/gpu_busy_percent; do
    if [ -r "$p" ]; then
        dev_dir="$(dirname "$p")"
        gpu="$(cat "$p" 2>/dev/null)"
        if [ -r "$dev_dir/mem_info_vram_used" ] && [ -r "$dev_dir/mem_info_vram_total" ]; then
            mem_used="$(cat "$dev_dir/mem_info_vram_used" 2>/dev/null)"
            mem_total="$(cat "$dev_dir/mem_info_vram_total" 2>/dev/null)"
        fi
        break
    fi
done

# 2. Fallback a NVIDIA (vía nvidia-smi para PC de escritorio)
if [ -z "$gpu" ] && command -v nvidia-smi >/dev/null 2>&1; then
    IFS=', ' read -r gpu mem_used mem_total <<< "$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null)"
fi

if [ "$1" = "gpu" ]; then
    echo "${gpu:-0}%"
elif [ "$1" = "vram" ]; then
    if [ -n "$mem_used" ] && [ -n "$mem_total" ] && [ "$mem_total" -gt 0 ]; then
        echo "$(( mem_used * 100 / mem_total ))%"
    else
        echo "0%"
    fi
else
    if [ -n "$gpu" ] && [ -n "$mem_used" ] && [ -n "$mem_total" ] && [ "$mem_total" -gt 0 ]; then
        echo "${gpu}%|$(( mem_used * 100 / mem_total ))%"
    else
        echo "0%|0%"
    fi
fi
