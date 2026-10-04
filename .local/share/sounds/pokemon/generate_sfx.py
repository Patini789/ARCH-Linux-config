import wave
import math
import struct
import os

SAMPLE_RATE = 44100

def create_wave(filename, samples):
    with wave.open(filename, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        for s in samples:
            val = max(-32767, min(32767, int(s * 32767)))
            wav.writeframes(struct.pack('<h', val))

def square_wave(freq, duration, duty=0.5, volume=0.3):
    num_samples = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(num_samples):
        t = i / SAMPLE_RATE
        phase = (t * freq) % 1.0
        val = volume if phase < duty else -volume
        # Smooth decay envelope
        env = max(0.0, 1.0 - (i / num_samples))
        samples.append(val * env)
    return samples

def shiny_sparkle():
    # Sparkle shimmer: rapid cascading high-pitch arpeggio
    notes = [1046.5, 1318.5, 1567.98, 1975.53, 2093.0, 2637.0, 3135.96, 4186.0]
    samples = []
    for f in notes:
        samples.extend(square_wave(f, 0.05, duty=0.25, volume=0.25))
    # Final shimmering chime
    for i in range(int(SAMPLE_RATE * 0.4)):
        t = i / SAMPLE_RATE
        env = max(0.0, 1.0 - (i / (SAMPLE_RATE * 0.4)))
        # Dual frequency sparkle
        s = 0.15 * math.sin(2 * math.pi * 3135.96 * t) + 0.15 * math.sin(2 * math.pi * 4186.0 * t)
        samples.append(s * env)
    return samples

def item_get():
    # Classic 4-note victory chime
    notes = [(523.25, 0.10), (659.25, 0.10), (783.99, 0.10), (1046.5, 0.35)]
    samples = []
    for f, d in notes:
        samples.extend(square_wave(f, d, duty=0.5, volume=0.35))
    return samples

def pokeball_blip():
    # Quick satisfying confirmation blip
    notes = [(880.0, 0.04), (1760.0, 0.08)]
    samples = []
    for f, d in notes:
        samples.extend(square_wave(f, d, duty=0.25, volume=0.3))
    return samples

def pokemon_center_heal():
    # Iconic 6-note heal melody
    notes = [
        (739.99, 0.14), # F#5
        (587.33, 0.14), # D5
        (493.88, 0.14), # B4
        (659.25, 0.14), # E5
        (880.00, 0.14), # A5
        (1174.66, 0.45) # D6
    ]
    samples = []
    for f, d in notes:
        samples.extend(square_wave(f, d, duty=0.5, volume=0.35))
    return samples

out_dir = "/home/patini/.local/share/sounds/pokemon"
os.makedirs(out_dir, exist_ok=True)

create_wave(os.path.join(out_dir, "shiny_sparkle.wav"), shiny_sparkle())
create_wave(os.path.join(out_dir, "item_get.wav"), item_get())
create_wave(os.path.join(out_dir, "pokeball_blip.wav"), pokeball_blip())
create_wave(os.path.join(out_dir, "pokemon_center_heal.wav"), pokemon_center_heal())
print("Sonidos Pokemon generados con éxito en:", out_dir)
