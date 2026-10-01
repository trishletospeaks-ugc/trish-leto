#!/usr/bin/env python3
"""
Build the favicons and the Open Graph image.

    python3 tools/make_icons.py

  docs/favicon.ico, apple-touch-icon.png, android-chrome-192.png, android-chrome-512.png
      Drawn with Pillow from the same geometry as favicon.svg (64-unit grid).
  docs/assets/img/og-image.jpg  (1200x630)
      Screenshot of tools/og.html in headless Chrome. Run tools/make_images.py
      first, because og.html uses the optimized headshot.
"""
import os
import subprocess
import tempfile
from urllib.parse import quote

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
DOCS = os.path.join(SITE, "docs")  # the published folder
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

INK, PAPER, CORAL_SOFT = "#17193b", "#fbf7f1", "#ff8aa3"


def draw_icon(size, rounded=True):
    s = 8  # supersample
    n = size * s
    k = n / 64
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if rounded:
        d.rounded_rectangle((0, 0, n - 1, n - 1), radius=round(14 * k), fill=INK)
    else:
        d.rectangle((0, 0, n, n), fill=INK)
    r = lambda x0, y0, x1, y1, c: d.rectangle((round(x0 * k), round(y0 * k), round(x1 * k) - 1, round(y1 * k) - 1), fill=c)
    # T
    r(8, 14, 34, 22, PAPER)
    r(16.5, 14, 25.5, 50, PAPER)
    # L
    r(38, 14, 46.5, 50, CORAL_SOFT)
    r(38, 42, 56, 50, CORAL_SOFT)
    return im.resize((size, size), Image.LANCZOS)


def icons():
    draw_icon(180, rounded=False).convert("RGB").save(os.path.join(DOCS, "apple-touch-icon.png"), optimize=True)
    draw_icon(192).save(os.path.join(DOCS, "android-chrome-192.png"), optimize=True)
    draw_icon(512).save(os.path.join(DOCS, "android-chrome-512.png"), optimize=True)
    big = draw_icon(256)
    big.save(os.path.join(DOCS, "favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    print("icons written")


def og_image():
    url = "file://" + quote(os.path.join(HERE, "og.html"))
    with tempfile.TemporaryDirectory() as tmp:
        png = os.path.join(tmp, "og.png")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=1", "--window-size=1200,630",
                        "--virtual-time-budget=6000", f"--screenshot={png}", url],
                       check=True, capture_output=True)
        im = Image.open(png).convert("RGB")
        if im.size != (1200, 630):
            im = im.crop((0, 0, 1200, 630))
        out = os.path.join(DOCS, "assets", "img", "og-image.jpg")
        im.save(out, "JPEG", quality=86, optimize=True, progressive=True)
        print(f"{out} {im.size} {os.path.getsize(out) // 1024} KB")


if __name__ == "__main__":
    icons()
    og_image()
