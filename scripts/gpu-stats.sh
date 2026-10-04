#!/bin/bash
IFS=', ' read -r gpu mem_used mem_total <<< "$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null)"
if [ "$1" = "gpu" ]; then
    echo "${gpu:-0}%"
elif [ "$1" = "vram" ]; then
    if [ -n "$mem_used" ] && [ -n "$mem_total" ] && [ "$mem_total" -gt 0 ]; then
        echo "$(( mem_used * 100 / mem_total ))%"
    else
        echo "0%"
    fi
else
    echo "0%"
fi
