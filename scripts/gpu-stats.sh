#!/bin/bash
IFS=', ' read -r gpu mem_used mem_total <<< "$(nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null)"
if [ -n "$gpu" ] && [ -n "$mem_used" ] && [ -n "$mem_total" ]; then
    vram_perc=$(( mem_used * 100 / mem_total ))
    echo "${gpu}%|${vram_perc}%"
else
    echo "0%|0%"
fi
