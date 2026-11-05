#!/bin/bash
sleep 2
openrgb --device "Logitech G213" --mode Direct --color 00ffff \
        --device "G502" --mode Static --color 00ffff \
        --device "Kingston" --mode Static --color 00ffff \
        --device "ASUS" --mode Static --color 00ffff >/dev/null 2>&1
