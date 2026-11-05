#!/usr/bin/env python3
"""
🌸 Gardevoir Weather Engine - Open-Meteo Integration
Proporciona datos meteorológicos en tiempo real utilizando la API abierta y gratuita
de Open-Meteo (sin API key), con geolocalización automática por IP, caché local
de 15 minutos en disco y resiliencia offline completa.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

HOME = str(Path.home())
CONFIG_DIR = os.path.join(HOME, ".config/gardevoir-weather")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
CACHE_DIR = os.path.join(HOME, ".cache/gardevoir-weather")
CACHE_FILE = os.path.join(CACHE_DIR, "weather.json")

# Códigos meteorológicos WMO mapeados a glifos Nerd Font y español
WMO_MAP = {
    0: ("󰖙", "Despejado"),
    1: ("󰖕", "Mayormente despejado"),
    2: ("󰖕", "Parcialmente nublado"),
    3: ("󰖐", "Nublado"),
    45: ("󰖑", "Niebla"),
    48: ("󰖑", "Niebla con escarcha"),
    51: ("󰖗", "Llovizna ligera"),
    53: ("󰖗", "Llovizna moderada"),
    55: ("󰖗", "Llovizna densa"),
    56: ("󰖗", "Llovizna helada"),
    57: ("󰖗", "Llovizna helada densa"),
    61: ("󰖖", "Lluvia ligera"),
    63: ("󰖖", "Lluvia moderada"),
    65: ("󰖖", "Lluvia intensa"),
    66: ("󰖖", "Lluvia helada ligera"),
    67: ("󰖖", "Lluvia helada intensa"),
    71: ("󰼶", "Nevada ligera"),
    73: ("󰼶", "Nevada moderada"),
    75: ("󰼶", "Nevada intensa"),
    77: ("󰼶", "Granos de nieve"),
    80: ("󰖖", "Chubascos ligeros"),
    81: ("󰖖", "Chubascos moderados"),
    82: ("󰖖", "Chubascos violentos"),
    85: ("󰼶", "Chubascos de nieve"),
    86: ("󰼶", "Chubascos de nieve intensos"),
    95: ("󰖓", "Tormenta eléctrica"),
    96: ("󰖓", "Tormenta con granizo ligero"),
    99: ("󰖓", "Tormenta con granizo fuerte"),
}


def load_config():
    defaults = {
        "auto_location": True,
        "city": "Guadalajara",
        "latitude": 20.638,
        "longitude": -103.348,
        "cache_ttl_seconds": 900  # 15 minutos
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                defaults.update(json.load(f))
        except Exception:
            pass
    return defaults


def save_config(cfg):
    try:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def detect_location(cfg):
    """Detecta la ubicación aproximada mediante IP sin API key."""
    if not cfg.get("auto_location", True):
        return cfg.get("latitude", 20.638), cfg.get("longitude", -103.348), cfg.get("city", "Guadalajara")

    try:
        req = urllib.request.Request(
            "http://ip-api.com/json/",
            headers={"User-Agent": "GardevoirWeather/1.0"}
        )
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("status") == "success":
                lat = float(data.get("lat", cfg.get("latitude", 20.638)))
                lon = float(data.get("lon", cfg.get("longitude", -103.348)))
                city = data.get("city", cfg.get("city", "Guadalajara"))
                # Actualizar config en disco
                cfg["latitude"] = lat
                cfg["longitude"] = lon
                cfg["city"] = city
                save_config(cfg)
                return lat, lon, city
    except Exception:
        pass

    return cfg.get("latitude", 20.638), cfg.get("longitude", -103.348), cfg.get("city", "Guadalajara")


def get_cached_weather():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def save_cached_weather(data):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": time.time(),
                "data": data
            }, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def fetch_weather(force=False):
    cfg = load_config()
    ttl = cfg.get("cache_ttl_seconds", 900)

    # 1. Comprobar caché en disco
    cached = get_cached_weather()
    if cached and not force:
        age = time.time() - cached.get("timestamp", 0)
        if age < ttl:
            return cached.get("data")

    # 2. Obtener coordenadas
    lat = cfg.get("latitude")
    lon = cfg.get("longitude")
    city = cfg.get("city", "Guadalajara")

    if lat is None or lon is None or cfg.get("auto_location", True):
        lat, lon, city = detect_location(cfg)

    # 3. Consultar Open-Meteo
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
        f"&timezone=auto"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "GardevoirWeather/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            raw = json.loads(resp.read().decode())
            cur = raw.get("current", {})

            code = cur.get("weather_code", 0)
            icon, desc = WMO_MAP.get(code, ("󰖐", "Nublado"))

            weather_data = {
                "city": city,
                "temperature": round(cur.get("temperature_2m", 0)),
                "apparent_temperature": round(cur.get("apparent_temperature", 0)),
                "humidity": cur.get("relative_humidity_2m", 0),
                "wind_speed": round(cur.get("wind_speed_10m", 0)),
                "precipitation": cur.get("precipitation", 0.0),
                "weather_code": code,
                "icon": icon,
                "description": desc,
                "offline": False
            }

            save_cached_weather(weather_data)
            return weather_data

    except Exception:
        # En caso de fallo o desconexión, retornar caché anterior si existe
        if cached and "data" in cached:
            fallback = cached["data"]
            fallback["offline"] = True
            return fallback

    # Fallback predeterminado seguro si nunca hubo conexión
    return {
        "city": city or "Local",
        "temperature": 22,
        "apparent_temperature": 22,
        "humidity": 50,
        "wind_speed": 5,
        "precipitation": 0.0,
        "weather_code": 2,
        "icon": "󰖕",
        "description": "Clima no disponible",
        "offline": True
    }


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "text"
    force = "--refresh" in sys.argv or "-r" in sys.argv

    data = fetch_weather(force=force)

    icon = data.get("icon", "󰖕")
    temp = data.get("temperature", 22)
    desc = data.get("description", "Despejado")
    feels = data.get("apparent_temperature", temp)
    hum = data.get("humidity", 50)
    wind = data.get("wind_speed", 5)
    city = data.get("city", "Guadalajara")

    if mode == "icon":
        # Solo el icono Nerd Font para el reloj de escritorio
        print(icon)

    elif mode == "short":
        # Icono + Temperatura
        print(f"{icon} {temp}°C")

    elif mode == "conky":
        # Salida formateada con colores Conky
        # color4 = acento rosa, color2 = blanco texto, color3 = gris secundario
        print(f"${{color4}}{icon} ${{color2}}{temp}°C ${{color3}}{desc}  ${{color4}} ${{color2}}{hum}%")

    elif mode == "detail":
        # Detalle completo para TimeDex
        print(f"{icon}  {temp}°C • {desc} • Sensación {feels}°C • Humedad {hum}% ({city})")

    elif mode == "json":
        print(json.dumps(data, ensure_ascii=False))

    else:  # "text"
        print(f"{icon} {temp}°C {desc} • Sensación {feels}°C • Viento {wind} km/h • Humedad {hum}% ({city})")


if __name__ == "__main__":
    main()
