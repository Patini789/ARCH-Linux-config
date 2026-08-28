#!/bin/bash
sleep 2
openrgb --device 1 --mode Direct --color 00ffff >/dev/null 2>&1
openrgb --device 0 --mode Static --color 00ffff >/dev/null 2>&1
