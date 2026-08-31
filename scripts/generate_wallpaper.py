#!/usr/bin/env python3
"""Genera lo sfondo StradilabOS in stile Big Sur (requisito D, §6.6).

Produce un'onda/gradiente originale con la palette StradiLab
(bordeaux → navy → crema), senza alcun asset Apple:
  - stradilabos-wallpaper-v3.svg          sorgente vettoriale
  - stradilabos-wallpaper-v3.png          1920×1080 (principale)
  - stradilabos-wallpaper-v3-1366x768.png
  - stradilabos-wallpaper-v3-2560x1440.png

I file PNG vengono tracciati con Pillow; il sorgente SVG è scritto come testo.
Eseguibile anche offline, senza dipendenze esterne oltre a Pillow.
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
BG_DIR = PROJECT_ROOT / "config/includes.chroot/usr/share/backgrounds/stradilabos"

# Palette StradiLab (docs/BRAND-STRADILAB.md).
BORDEAUX = (155, 35, 53)
NAVY = (27, 58, 107)
NAVY_DEEP = (16, 32, 58)
CREMA = (246, 244, 239)
AVORIO = (255, 255, 255)
ACCENT_BLUE = (51, 104, 181)
ACCENT_GOLD = (212, 168, 90)

SVG_SOURCE = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="1920" height="1080" viewBox="0 0 1920 1080" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="cielo" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#1b3a6b"/>
      <stop offset="0.55" stop-color="#2c4a6e"/>
      <stop offset="1" stop-color="#9b2335"/>
    </linearGradient>
    <linearGradient id="onda1" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#9b2335" stop-opacity="0.85"/>
      <stop offset="1" stop-color="#f6f4ef" stop-opacity="0.55"/>
    </linearGradient>
    <linearGradient id="onda2" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#1b3a6b" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#f6f4ef" stop-opacity="0.35"/>
    </linearGradient>
  </defs>
  <rect width="1920" height="1080" fill="url(#cielo)"/>
  <path d="M0 720 C480 640 800 800 1280 740 C1600 690 1800 760 1920 700 L1920 1080 L0 1080 Z" fill="url(#onda1)"/>
  <path d="M0 820 C400 760 880 900 1360 840 C1640 810 1840 860 1920 830 L1920 1080 L0 1080 Z" fill="url(#onda2)"/>
  <path d="M0 920 C520 880 960 980 1440 930 C1720 900 1840 950 1920 930 L1920 1080 L0 1080 Z" fill="#16130f" fill-opacity="0.18"/>
  <circle cx="1540" cy="280" r="180" fill="#f6f4ef" fill-opacity="0.12"/>
</svg>
"""


def _blend(top: tuple[int, int, int], bottom: tuple[int, int, int], alpha: float) -> tuple[int, int, int]:
    return tuple(round(top[i] * alpha + bottom[i] * (1 - alpha)) for i in range(3))


def _draw_waves(size: tuple[int, int]) -> Image.Image:
    """Disegna l'onda Big Sur con la palette StradiLab, senza asset esterni."""
    width, height = size
    base = Image.new("RGB", size, NAVY)

    # Cielo: gradiente verticale navy → bordeaux.
    top = NAVY_DEEP
    bottom = BORDEAUX
    for y in range(height):
        t = y / max(1, height - 1)
        color = _blend(top, bottom, t)
        base.paste(color, (0, y, width, y + 1))
    base = base.filter(ImageFilter.GaussianBlur(4))

    wave = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(wave)

    def curve(base_y: int, amp: int, phase: float, color: tuple, alpha: int) -> None:
        points = []
        for x in range(0, width + 1, 4):
            t = x / max(1, width - 1)
            y = base_y + amp * math.sin(2 * math.pi * (t * 1.6 + phase))
            points.append((x, y))
        points += [(width, height), (0, height)]
        draw.polygon(points, fill=(*color, alpha))

    # Strati ondulati: bordeaux → crema, navy → crema, accento scuro.
    curve(int(height * 0.68), 110, 0.0, BORDEAUX, 210)
    curve(int(height * 0.76), 90, 0.35, NAVY, 220)
    curve(int(height * 0.86), 70, 0.68, ACCENT_BLUE, 170)
    curve(int(height * 0.93), 46, 0.12, (22, 19, 15), 150)

    # Alone di luce in alto a destra, come un sole tenue sull'onda.
    glow = Image.new("RGBA", size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    cx, cy, r = int(width * 0.8), int(height * 0.27), int(max(width, height) * 0.22)
    glow_draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*CREMA, 46))
    glow = glow.filter(ImageFilter.GaussianBlur(160))
    wave = Image.alpha_composite(wave, glow)

    return Image.alpha_composite(base.convert("RGBA"), wave).convert("RGB")


def main() -> int:
    BG_DIR.mkdir(parents=True, exist_ok=True)
    (BG_DIR / "stradilabos-wallpaper-v3.svg").write_text(SVG_SOURCE, encoding="utf-8")

    resolutions = {
        "stradilabos-wallpaper-v3.png": (1920, 1080),
        "stradilabos-wallpaper-v3-1366x768.png": (1366, 768),
        "stradilabos-wallpaper-v3-2560x1440.png": (2560, 1440),
    }
    for name, size in resolutions.items():
        _draw_waves(size).save(BG_DIR / name, optimize=True)

    print("Sfondo Big Sur generato: 1 SVG +", len(resolutions), "PNG.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())